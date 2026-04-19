import json
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from nichefinder_cli.main import app
from nichefinder_core.models import (
    Article,
    CompetitorPage,
    ContentBrief,
    ContentType,
    Keyword,
    OpportunityScore,
    SearchIntent,
    SerpResult,
    SiteConfig,
)
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


def _runtime(tmp_path: Path) -> tuple[Settings, SiteConfig]:
    db_path = tmp_path / "seo.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    create_db_and_tables(settings)
    return settings, SiteConfig()


def test_research_command_stores_keywords_and_prints_ranked_output(monkeypatch, tmp_path: Path):
    settings, site_config = _runtime(tmp_path)

    async def fake_run_full_pipeline(seed_keyword: str, site_config_data: dict, services, repository, location: str = "Montreal, Quebec, Canada"):
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
        "nichefinder_cli.main.get_runtime",
        lambda: (settings, site_config, get_session(settings)),
    )
    monkeypatch.setattr("nichefinder_cli.main.build_services", lambda settings, repository: fake_services)
    monkeypatch.setattr("nichefinder_cli.main.run_full_pipeline", fake_run_full_pipeline)

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
        "nichefinder_cli.main.get_runtime",
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
