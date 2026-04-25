import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from nichefinder_cli.free_validation import run_free_validation_pipeline
from nichefinder_cli.main import app
from nichefinder_cli.runtime import delete_profile, get_runtime, resolve_runtime_settings
from nichefinder_cli.viewer_profile_data import load_profiles
from nichefinder_cli.workflows import run_full_pipeline
from nichefinder_core.free_validation_context import FreeValidationContext, FrozenShortlistItem
from nichefinder_core.models import (
    Article,
    BuyerProblem,
    CompetitorPage,
    ContentBrief,
    ContentType,
    Keyword,
    OpportunityScore,
    SearchConsoleRecord,
    SearchIntent,
    SerpResult,
    SiteConfig,
)
from nichefinder_core.models.site import save_site_config
from nichefinder_core.noise_memory import approve_noise_entries, approve_training_entries, record_validation_run
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


def _root_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'seo.db'}",
        site_config_path=tmp_path / "site_config.json",
        cache_dir=tmp_path / "cache",
        profiles_dir=tmp_path / "profiles",
        active_profile_path=tmp_path / "profiles" / ".active",
        articles_dir=tmp_path / "outputs" / "articles",
        reports_dir=tmp_path / "outputs" / "reports",
        audits_dir=tmp_path / "outputs" / "audits",
    )


def _runtime(tmp_path: Path) -> tuple[Settings, SiteConfig]:
    settings = _root_settings(tmp_path)
    create_db_and_tables(settings)
    return settings, SiteConfig()


def test_research_command_stores_keywords_and_prints_ranked_output(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)

    async def fake_run_full_pipeline(seed_keyword: str, site_config_data: dict, services, repository, location: str = "Montreal, Quebec, Canada", console=None):
        keyword = repository.upsert_keyword(
            Keyword(
                term="ai tool development consultant",
                seed_keyword=seed_keyword,
                source="test",
                opportunity_score=72.5,
            )
        )
        opportunity = OpportunityScore(
            keyword_id=keyword.id,
            keyword_term=keyword.term,
            volume_score=60,
            difficulty_score=80,
            trend_score=50,
            intent_score=80,
            competition_score=70,
            composite_score=72.5,
            why_good_fit="Strong fit",
            content_angle="How I build AI tools for clients",
            priority="high",
            action="create_new",
        )
        return {
            "analyses": [
                {
                    "synthesis": SimpleNamespace(
                        opportunity_score=opportunity,
                        should_create_content=False,
                    )
                }
            ]
        }

    fake_services = SimpleNamespace(
        gemini=SimpleNamespace(
            get_usage_stats=lambda: {"prompt_tokens": 0, "response_tokens": 0}
        ),
        scraper=SimpleNamespace(close=lambda: None),
    )

    async def fake_close():
        return None

    fake_services.scraper.close = fake_close

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.research.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr(
        "nichefinder_cli.commands.root.research.build_services",
        lambda settings, repository: fake_services,
    )
    monkeypatch.setattr("nichefinder_cli.commands.root.research.run_full_pipeline", fake_run_full_pipeline)

    result = CliRunner().invoke(app, ["research", "AI tool development"])

    assert result.exit_code == 0
    assert "Opportunity Report" in result.output
    assert "72.5" in result.output
    assert "high" in result.output.lower()
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keywords = repository.list_keywords()
        assert len(keywords) == 1
        assert keywords[0].term == "ai tool development consultant"


def test_validate_free_command_runs_without_paid_validation(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)

    async def fake_run_free_validation_pipeline(
        seed_keyword: str,
        site_config_data: dict,
        services,
        repository,
        location: str = "Montreal, Quebec, Canada",
        sources: tuple[str, ...] = ("ddgs", "bing", "yahoo"),
        console=None,
    ):
        repository.upsert_keyword(
            Keyword(
                term="how much does a website cost in montreal",
                seed_keyword=seed_keyword,
                source="test",
                opportunity_score=68.0,
            )
        )
        return {"shortlist": [], "problem_validations": []}

    fake_services = SimpleNamespace(
        gemini=SimpleNamespace(
            get_usage_stats=lambda: {"prompt_tokens": 0, "response_tokens": 0}
        ),
        scraper=SimpleNamespace(close=lambda: None),
    )

    async def fake_close():
        return None

    fake_services.scraper.close = fake_close

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.build_services",
        lambda settings, repository: fake_services,
    )
    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.run_free_validation_pipeline",
        fake_run_free_validation_pipeline,
    )

    result = CliRunner().invoke(app, ["validate-free", "website cost"])

    assert result.exit_code == 0
    assert "DDGS this month" in result.output
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keywords = repository.list_keywords()
        assert len(keywords) == 1
        assert keywords[0].term == "how much does a website cost in montreal"


def test_validate_source_commands_pass_single_bucket(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    calls: list[tuple[str, tuple[str, ...]]] = []

    async def fake_run_free_validation_pipeline(
        seed_keyword: str,
        site_config_data: dict,
        services,
        repository,
        location: str = "Montreal, Quebec, Canada",
        sources: tuple[str, ...] = ("ddgs", "bing", "yahoo"),
        console=None,
    ):
        calls.append((seed_keyword, sources))
        return {"shortlist": [], "problem_validations": []}

    fake_services = SimpleNamespace(
        gemini=SimpleNamespace(
            get_usage_stats=lambda: {"prompt_tokens": 0, "response_tokens": 0}
        ),
        scraper=SimpleNamespace(close=lambda: None),
    )

    async def fake_close():
        return None

    fake_services.scraper.close = fake_close

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.build_services",
        lambda settings, repository: fake_services,
    )
    monkeypatch.setattr(
        "nichefinder_cli.commands.root.shared.run_free_validation_pipeline",
        fake_run_free_validation_pipeline,
    )

    runner = CliRunner()
    ddgs_result = runner.invoke(app, ["validate-ddgs", "website cost"])
    bing_result = runner.invoke(app, ["validate-bing", "website cost"])
    yahoo_result = runner.invoke(app, ["validate-yahoo", "website cost"])

    assert ddgs_result.exit_code == 0
    assert bing_result.exit_code == 0
    assert yahoo_result.exit_code == 0
    assert calls == [
        ("website cost", ("ddgs",)),
        ("website cost", ("bing",)),
        ("website cost", ("yahoo",)),
    ]
    assert "DDGS this month" in ddgs_result.output
    assert "Bing this month" in bing_result.output
    assert "Yahoo this month" in yahoo_result.output


def test_review_noise_and_approve_noise_commands(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    for _ in range(2):
        record_validation_run(
            settings,
            site_config=site_config.model_dump(),
            seed_keyword="how much does a business website cost in montreal",
            location="Montreal, Quebec, Canada",
            shortlist=[SimpleNamespace(term="web design cost montreal")],
            keyword_validations=[],
            article_evidence=[SimpleNamespace(query="seed", suggested_secondary_keywords=["mobile optimization"])],
        )

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.reviews.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )

    runner = CliRunner()
    review = runner.invoke(app, ["review-noise", "--min-runs", "2"])
    approve = runner.invoke(
        app,
        [
            "approve-noise",
            "--keyword-phrase",
            "web design",
            "--secondary-phrase",
            "mobile optimization",
            "--domain",
            "dictionary.com",
        ],
    )

    assert review.exit_code == 0
    assert "web design" in review.output
    assert approve.exit_code == 0
    profile = approve_noise_entries(
        settings,
        site_config=site_config.model_dump(),
        keyword_phrases=[],
        secondary_phrases=[],
        domains=[],
    )
    assert "web design" in profile.keyword_phrases
    assert "mobile optimization" in profile.secondary_phrases
    assert "dictionary.com" in profile.domains


def test_review_training_and_approve_training_commands(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    validations = [
        SimpleNamespace(
            query="food cost percentage restaurant",
            score=8,
            degraded=False,
            top_domains=["restaurant.org"],
        ),
        SimpleNamespace(
            query="custom software development restaurant",
            score=-2,
            degraded=False,
            top_domains=["dictionary.com"],
        ),
    ]
    evidence = [SimpleNamespace(query="food cost percentage restaurant", suggested_secondary_keywords=["portion control"], source_urls=["https://restaurant.org/guide"])]
    for _ in range(2):
        record_validation_run(
            settings,
            site_config=site_config.model_dump(),
            seed_keyword="how to reduce food cost in a restaurant",
            location="Montreal, Quebec, Canada",
            shortlist=[SimpleNamespace(term="custom software development restaurant", score=20)],
            keyword_validations=validations,
            article_evidence=evidence,
        )

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.reviews.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )

    runner = CliRunner()
    review = runner.invoke(app, ["review-training", "--min-runs", "2"])
    approve = runner.invoke(
        app,
        [
            "approve-training",
            "--valid-keyword-phrase",
            "food cost percentage",
            "--valid-secondary-phrase",
            "portion control",
            "--trusted-domain",
            "restaurant.org",
            "--noise-keyword-phrase",
            "custom software development",
            "--noise-domain",
            "dictionary.com",
        ],
    )

    assert review.exit_code == 0
    assert "Validity" in review.output
    assert "food cost percentage" in review.output
    assert "restaurant.org" in review.output
    assert "custom software development" in review.output
    assert approve.exit_code == 0
    profile = approve_training_entries(
        settings,
        site_config=site_config.model_dump(),
        valid_keyword_phrases=[],
        valid_secondary_phrases=[],
        trusted_domains=[],
        noise_keyword_phrases=[],
        noise_secondary_phrases=[],
        noise_domains=[],
    )
    assert "food cost percentage" in profile.valid_keyword_phrases
    assert "portion control" in profile.valid_secondary_phrases
    assert "restaurant.org" in profile.trusted_domains
    assert "custom software development" in profile.keyword_phrases
    assert "dictionary.com" in profile.domains


def test_profile_commands_and_final_review(monkeypatch, tmp_path: Path):
    settings = _root_settings(tmp_path)
    monkeypatch.setattr("nichefinder_cli.runtime.get_settings", lambda: settings)

    runner = CliRunner()
    create_first = runner.invoke(app, ["profile-init", "restaurant", "--use"])
    create_second = runner.invoke(app, ["profile-init", "salon"])
    use_first = runner.invoke(app, ["profile-use", "restaurant"])
    listed = runner.invoke(app, ["profile-list"])

    assert create_first.exit_code == 0
    assert create_second.exit_code == 0
    assert use_first.exit_code == 0
    assert listed.exit_code == 0
    assert "restaurant" in listed.output
    assert "salon" in listed.output
    assert "active" in listed.output

    restaurant_settings, restaurant_site, _ = get_runtime("restaurant")
    salon_settings, salon_site, _ = get_runtime("salon")
    record_validation_run(
        restaurant_settings,
        site_config=restaurant_site.model_dump(),
        seed_keyword="reduce food cost",
        location="Montreal, Quebec, Canada",
        shortlist=[],
        keyword_validations=[SimpleNamespace(query="food cost percentage restaurant", score=8, degraded=False, top_domains=["restaurant.org"])],
        article_evidence=[],
    )
    record_validation_run(
        salon_settings,
        site_config=salon_site.model_dump(),
        seed_keyword="salon client retention",
        location="Montreal, Quebec, Canada",
        shortlist=[],
        keyword_validations=[SimpleNamespace(query="salon client retention strategies", score=8, degraded=False, top_domains=["restaurant.org"])],
        article_evidence=[],
    )
    approve_training_entries(
        restaurant_settings,
        site_config=restaurant_site.model_dump(),
        trusted_domains=["restaurant.org"],
    )
    approve_training_entries(
        salon_settings,
        site_config=salon_site.model_dump(),
        trusted_domains=["restaurant.org"],
    )

    review = runner.invoke(app, ["final-review", "restaurant", "salon", "--min-runs", "1", "--limit", "3"])

    assert review.exit_code == 0
    assert "Final Review" in review.output
    assert "restaurant" in review.output
    assert "salon" in review.output
    assert "restaurant.org" in review.output


def test_db_reset_clears_profile_state(monkeypatch, tmp_path: Path):
    settings = _root_settings(tmp_path)
    monkeypatch.setattr("nichefinder_cli.runtime.get_settings", lambda: settings)
    runner = CliRunner()
    runner.invoke(app, ["profile-init", "restaurant", "--use"])
    active_settings = resolve_runtime_settings("restaurant")
    db_path = tmp_path / "profiles" / "restaurant" / "seo.db"
    create_db_and_tables(active_settings)
    active_settings.resolved_cache_dir.mkdir(parents=True, exist_ok=True)
    active_settings.resolve_path(active_settings.outputs_dir).mkdir(parents=True, exist_ok=True)
    (active_settings.resolved_cache_dir / "tmp.json").write_text("{}", encoding="utf-8")
    (active_settings.resolve_path(active_settings.outputs_dir) / "report.txt").write_text("x", encoding="utf-8")

    result = runner.invoke(app, ["db", "reset", "--all-state"])

    assert result.exit_code == 0
    assert active_settings.resolved_cache_dir.exists() is False
    assert active_settings.resolve_path(active_settings.outputs_dir).exists() is False
    assert db_path.exists()


def test_delete_profile_does_not_reimport_leftover_runtime_directory(monkeypatch, tmp_path: Path):
    settings = _root_settings(tmp_path)
    monkeypatch.setattr("nichefinder_cli.runtime.get_settings", lambda: settings)
    monkeypatch.setattr("nichefinder_cli.runtime.rmtree", lambda *_args, **_kwargs: None)

    runner = CliRunner()
    created = runner.invoke(app, ["profile-init", "restaurant"])

    assert created.exit_code == 0
    assert (tmp_path / "profiles" / "restaurant" / "site_config.json").exists()

    delete_profile("restaurant")
    profiles = load_profiles()

    assert [profile["slug"] for profile in profiles["profiles"]] == ["default"]
    assert (tmp_path / "profiles" / "restaurant").exists()
    assert (tmp_path / "profiles" / "restaurant" / "site_config.json").exists() is False


def test_load_profiles_keeps_default_runtime_separate_from_active_profile(monkeypatch, tmp_path: Path):
    settings = _root_settings(tmp_path)
    monkeypatch.setattr("nichefinder_cli.runtime.get_settings", lambda: settings)

    runner = CliRunner()
    assert runner.invoke(app, ["profile-init", "restaurant", "--use"]).exit_code == 0

    profiles = load_profiles()
    default_profile = next(item for item in profiles["profiles"] if item["slug"] == "default")
    restaurant_profile = next(item for item in profiles["profiles"] if item["slug"] == "restaurant")

    assert profiles["active_profile"] == "restaurant"
    assert default_profile["database_url"] == settings.database_url
    assert restaurant_profile["database_url"].endswith("/profiles/restaurant/seo.db")
    assert default_profile["database_url"] != restaurant_profile["database_url"]


def test_load_profiles_initializes_empty_profile_database(monkeypatch, tmp_path: Path):
    settings = _root_settings(tmp_path)
    monkeypatch.setattr("nichefinder_cli.runtime.get_settings", lambda: settings)

    runner = CliRunner()
    assert runner.invoke(app, ["profile-init", "restaurant", "--use"]).exit_code == 0

    stray_dir = tmp_path / "profiles" / "stray-profile"
    stray_dir.mkdir(parents=True, exist_ok=True)
    save_site_config(stray_dir / "site_config.json", SiteConfig(site_name="Stray", site_url="https://example.com"))
    (stray_dir / "seo.db").touch()

    profiles = load_profiles()
    stray_profile = next(item for item in profiles["profiles"] if item["slug"] == "stray-profile")

    assert stray_profile["site_name"] == "Stray"
    assert stray_profile["database_url"].endswith("/profiles/stray-profile/seo.db")
    assert (stray_dir / "seo.db").exists()


def test_monitor_sync_requires_gsc_credentials(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)

    monkeypatch.setattr(
        "nichefinder_cli.commands.monitoring.monitor.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )

    result = CliRunner().invoke(app, ["monitor", "sync"])

    assert result.exit_code == 1
    assert "GSC_CREDENTIALS_PATH is not configured" in result.output


def test_monitor_sync_upserts_records_and_prints_summary(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    settings.gsc_credentials_path = tmp_path / "gsc.json"
    settings.gsc_property_url = "sc-domain:example.com"

    class FakeGscClient:
        def __init__(self, _settings):
            self._records = [
                SearchConsoleRecord(
                    query="website cost montreal",
                    page_url="https://example.com/website-cost",
                    impressions=100,
                    clicks=10,
                    ctr=0.1,
                    position=4.2,
                    snapshot_date=datetime(2026, 4, 18, tzinfo=timezone.utc).date(),
                    property_id="sc-domain:example.com",
                )
            ]

        def fetch_records(self, *, start_date, end_date, property_url=None):
            return [
                record.model_copy(
                    update={
                        "impressions": 120,
                        "clicks": 12,
                        "property_id": property_url or record.property_id,
                    }
                )
                for record in self._records
            ]

    monkeypatch.setattr(
        "nichefinder_cli.commands.monitoring.monitor.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr("nichefinder_cli.commands.monitoring.monitor.GscClient", FakeGscClient)

    runner = CliRunner()
    first = runner.invoke(app, ["monitor", "sync", "--days", "3"])
    second = runner.invoke(app, ["monitor", "sync", "--days", "3"])

    assert first.exit_code == 0
    assert "Inserted (new)" in first.output
    assert "1" in first.output
    assert second.exit_code == 0
    assert "Updated (refreshed)" in second.output
    with get_session(settings) as session:
        repository = SeoRepository(session)
        records = repository.list_search_console_records()
        assert len(records) == 1
        assert records[0].impressions == 120
        assert records[0].clicks == 12


def test_monitor_sync_handles_empty_result_set(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    settings.gsc_credentials_path = tmp_path / "gsc.json"

    class EmptyGscClient:
        def __init__(self, _settings):
            pass

        def fetch_records(self, *, start_date, end_date, property_url=None):
            return []

    monkeypatch.setattr(
        "nichefinder_cli.commands.monitoring.monitor.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr("nichefinder_cli.commands.monitoring.monitor.GscClient", EmptyGscClient)

    result = CliRunner().invoke(app, ["monitor", "sync"])

    assert result.exit_code == 0
    assert "No GSC rows returned for this date range." in result.output


def test_report_command_reads_local_keyword_and_article_state(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.upsert_keyword(
            Keyword(
                term="ai consultant portfolio",
                seed_keyword="ai consultant portfolio",
                source="manual",
                monthly_volume=500,
                difficulty_score=35,
                opportunity_score=68.0,
            )
        )
        repository.create_article(
            Article(
                keyword_id=keyword.id,
                title="AI Consultant Portfolio Guide",
                slug="ai-consultant-portfolio-guide",
                content_type=ContentType.HOW_TO,
                status="published",
                word_count=1200,
                file_path=str(tmp_path / "article.md"),
                published_url="https://example.com/post",
            ),
            "# Article",
        )

    monkeypatch.setattr(
        "nichefinder_cli.commands.root.reporting.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )

    result = CliRunner().invoke(app, ["report"])

    assert result.exit_code == 0
    assert "Opportunity Report" in result.output
    assert "ai consultant portfolio" in result.output
    assert "published_articles" in result.output


def test_keywords_inspect_shows_saved_research_artifacts(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.upsert_keyword(
            Keyword(
                term="custom ai tool development for small business",
                seed_keyword="custom ai tool development for small business",
                source="gemini_serpapi",
                search_intent=SearchIntent.COMMERCIAL,
                trend_direction="stable",
                opportunity_score=60.0,
            )
        )
        serp_result = repository.create_serp_result(
            SerpResult(
                keyword_id=keyword.id,
                features_json="{}",
                pages_json=json.dumps(
                    [
                        {
                            "position": 1,
                            "domain": "example.com",
                            "title": "Example Result",
                            "url": "https://example.com/result",
                        }
                    ]
                ),
                competition_analysis=json.dumps(
                    {
                        "rankable": True,
                        "competition_level": "medium",
                        "dominant_content_type": "article",
                        "recommended_content_angle": "Show concrete case studies.",
                    }
                ),
            )
        )
        repository.create_competitor_page(
            CompetitorPage(
                serp_result_id=serp_result.id,
                url="https://example.com/result",
                title="Example Result",
                word_count=1400,
                h1="Example H1",
                h2_list="Overview|Process",
                h3_list="Step 1|Step 2",
                questions_answered="How much does it cost?",
                internal_link_count=5,
                external_link_count=2,
                has_schema_markup=True,
                estimated_reading_time_min=6,
                content_summary="Case-study style page.",
            )
        )
        repository.save_content_brief(
            keyword.id,
            ContentBrief(
                target_keyword=keyword.term,
                secondary_keywords=["small business ai consultant"],
                content_type=ContentType.HOW_TO,
                suggested_title="How to build a custom AI tool for a small business",
                suggested_h2_structure=["Scope the workflow", "Build the prototype"],
                questions_to_answer=["What should the MVP include?"],
                word_count_target=1500,
                tone="practical",
                cta_type="contact_form",
                competing_urls=["https://example.com/result"],
                is_rewrite=False,
            ),
        )
        keyword_id = keyword.id

    monkeypatch.setattr(
        "nichefinder_cli.runtime.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )

    result = CliRunner().invoke(app, ["keywords", "inspect", keyword_id])

    assert result.exit_code == 0
    assert "Latest SERP Analysis" in result.output
    assert "Top SERP Pages" in result.output
    assert "Scraped Competitor Pages" in result.output
    assert "Latest Brief" in result.output
    assert "custom ai tool development for small business" in result.output


async def test_run_free_validation_pipeline_reuses_frozen_context_for_single_source(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    frozen = FreeValidationContext(
        seed_keyword="website cost montreal",
        location="Montreal, Quebec, Canada",
        created_at=datetime.now(timezone.utc),
        keywords_found=10,
        keywords_saved=8,
        buyer_problems=[
            BuyerProblem(
                problem="Pricing confusion",
                audience="owners",
                why_now="budgeting",
                article_angle="pricing guide",
                keyword_seed="website cost montreal",
                evidence_queries=[],
            )
        ],
        shortlist=[
            FrozenShortlistItem(
                keyword_id="k1",
                term="how much does a website cost in montreal",
                score=100.0,
                breakdown={"seed_fidelity": 30.0},
                canonical_key="website cost",
                selected=True,
                notes=["intent"],
            )
        ],
    )

    async def fake_validation(shortlist, buyer_problems, client, **kwargs):
        assert buyer_problems[0]["keyword_seed"] == "website cost montreal"
        return shortlist, [], []

    services = SimpleNamespace(
        settings=settings,
        keyword_agent=SimpleNamespace(run=lambda payload: (_ for _ in ()).throw(AssertionError("should not regenerate context"))),
        trend_agent=None,
        ddgs=SimpleNamespace(settings=SimpleNamespace(ddgs_ready=True)),
        bing=SimpleNamespace(settings=SimpleNamespace(bing_ready=False)),
        yahoo=SimpleNamespace(settings=SimpleNamespace(yahoo_ready=False)),
        scraper=SimpleNamespace(close=lambda: None),
    )

    monkeypatch.setattr("nichefinder_cli.free_validation.load_free_validation_context", lambda *args, **kwargs: frozen)
    monkeypatch.setattr("nichefinder_cli.free_validation.apply_ddgs_validation", fake_validation)

    with get_session(settings) as session:
        repository = SeoRepository(session)
        result = await run_free_validation_pipeline(
            "website cost montreal",
            site_config.model_dump(),
            services,
            repository,
            sources=("ddgs",),
            console=None,
        )

    assert result["shortlist"][0].term == "how much does a website cost in montreal"


async def test_run_full_pipeline_only_analyzes_selected_shortlist_keywords(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)
    settings.max_serp_keywords = 2
    settings.ddgs_enabled = False
    settings.bing_enabled = False
    settings.yahoo_enabled = False
    settings.tavily_api_key = ""

    with get_session(settings) as session:
        repository = SeoRepository(session)
        keywords = [
            repository.upsert_keyword(
                Keyword(
                    term=f"keyword {index}",
                    seed_keyword="seed",
                    source="test",
                    search_intent=SearchIntent.COMMERCIAL,
                )
            )
            for index in range(3)
        ]

        captured_max_keywords: list[int] = []
        analyzed: list[str] = []

        async def fake_shortlist(keyword_ids, repo, trend_agent, *, site_config, location, max_keywords, noise_profile=None):
            captured_max_keywords.append(max_keywords)
            return [
                SimpleNamespace(keyword_id=keywords[0].id, selected=True, term=keywords[0].term),
                SimpleNamespace(keyword_id=keywords[1].id, selected=False, term=keywords[1].term),
                SimpleNamespace(keyword_id=keywords[2].id, selected=True, term=keywords[2].term),
            ]

        class KeywordAgent:
            async def run(self, payload):
                buyer_problems = [
                    BuyerProblem(
                        problem="Pricing confusion",
                        audience="owners",
                        why_now="budgeting",
                        article_angle="pricing guide",
                        keyword_seed="website cost montreal",
                        evidence_queries=[],
                    )
                ]
                return SimpleNamespace(
                    buyer_problems=buyer_problems,
                    keywords_found=3,
                    keywords_saved=3,
                    keyword_ids=[keyword.id for keyword in keywords],
                    model_dump=lambda mode=None: {
                        "buyer_problems": [problem.model_dump() for problem in buyer_problems],
                        "keywords_found": 3,
                        "keywords_saved": 3,
                        "keyword_ids": [keyword.id for keyword in keywords],
                    },
                )

        class SerpAgent:
            async def run(self, payload):
                analyzed.append(payload.keyword_id)
                return SimpleNamespace(
                    serp_result_id=f"serp-{payload.keyword_id}",
                    competition_level="medium",
                    rankable=False,
                    difficulty_estimate=40,
                    pages_analyzed=10,
                    features_detected=[],
                    model_dump=lambda mode=None: {
                        "serp_result_id": f"serp-{payload.keyword_id}",
                        "competition_level": "medium",
                        "rankable": False,
                        "difficulty_estimate": 40,
                        "pages_analyzed": 10,
                        "features_detected": [],
                    },
                )

        class TrendAgent:
            async def run(self, payload):
                return SimpleNamespace(
                    direction="stable",
                    avg_interest=50.0,
                    model_dump=lambda mode=None: {"direction": "stable", "avg_interest": 50.0},
                )

        class AdsAgent:
            async def run(self, payload):
                return SimpleNamespace(model_dump=lambda mode=None: {})

        class SynthesisAgent:
            async def run(self, payload):
                return SimpleNamespace(
                    opportunity_score=OpportunityScore(
                        keyword_id=payload.keyword_id,
                        keyword_term=repository.get_keyword(payload.keyword_id).term,
                        volume_score=50,
                        difficulty_score=50,
                        trend_score=50,
                        intent_score=70,
                        competition_score=60,
                        composite_score=65,
                        why_good_fit="Strong fit",
                        content_angle="Pricing guide",
                        priority="medium",
                        action="create_new",
                    ),
                    should_create_content=False,
                )

        services = SimpleNamespace(
            settings=settings,
            keyword_agent=KeywordAgent(),
            trend_agent=TrendAgent(),
            serp_agent=SerpAgent(),
            ads_agent=AdsAgent(),
            competitor_agent=SimpleNamespace(),
            synthesis_agent=SynthesisAgent(),
        )

        monkeypatch.setattr("nichefinder_cli.workflows.build_trend_assisted_shortlist", fake_shortlist)

        result = await run_full_pipeline("seed", site_config.model_dump(), services, repository, console=None)

    assert captured_max_keywords == [2]
    assert analyzed == [keywords[0].id, keywords[2].id]
    assert [item["keyword"].id for item in result["analyses"]] == [keywords[0].id, keywords[2].id]
