import json
from pathlib import Path

from nichefinder_cli.viewer_data import (
    load_dashboard,
    load_keyword_clusters,
    load_keyword_detail,
    load_keywords,
    load_status,
)
from nichefinder_core.models import (
    Article,
    CompetitorPage,
    ContentBrief,
    ContentType,
    Keyword,
    SearchIntent,
    SerpResult,
)
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


def _settings(tmp_path: Path) -> Settings:
    settings = Settings(database_url=f"sqlite:///{tmp_path / 'seo.db'}")
    create_db_and_tables(settings)
    return settings


def test_dashboard_payload_handles_empty_database(tmp_path: Path):
    settings = _settings(tmp_path)

    payload = load_dashboard(settings)

    assert payload["summary"]["total_keywords"] == 0
    assert payload["keywords"] == []
    assert payload["articles"] == []


def test_keyword_detail_payload_includes_saved_work(tmp_path: Path):
    settings = _settings(tmp_path)
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.upsert_keyword(
            Keyword(
                term="ai roadmap consulting",
                seed_keyword="ai roadmap consulting",
                source="gemini_serpapi",
                search_intent=SearchIntent.COMMERCIAL,
                trend_direction="stable",
                opportunity_score=64.0,
            )
        )
        serp = repository.create_serp_result(
            SerpResult(
                keyword_id=keyword.id,
                features_json="{}",
                pages_json=json.dumps(
                    [{"position": 1, "domain": "example.com", "title": "Example", "url": "https://example.com"}]
                ),
                competition_analysis=json.dumps(
                    {"rankable": True, "competition_level": "medium", "recommended_content_angle": "Practical guide"}
                ),
            )
        )
        repository.create_competitor_page(
            CompetitorPage(
                serp_result_id=serp.id,
                url="https://example.com",
                title="Example",
                word_count=1200,
                h1="Example",
                h2_list="[]",
                h3_list="[]",
                questions_answered="[]",
                internal_link_count=2,
                external_link_count=1,
                has_schema_markup=False,
                estimated_reading_time_min=6,
                content_summary="Compact summary",
            )
        )
        repository.save_content_brief(
            keyword.id,
            ContentBrief(
                target_keyword=keyword.term,
                secondary_keywords=["ai product strategy"],
                content_type=ContentType.HOW_TO,
                suggested_title="AI roadmap consulting guide",
                suggested_h2_structure=["Why roadmaps matter"],
                questions_to_answer=["What should a roadmap include?"],
                word_count_target=1800,
                tone="practical",
                cta_type="contact_form",
                competing_urls=["https://example.com"],
                is_rewrite=False,
            ),
        )
        repository.create_article(
            Article(
                keyword_id=keyword.id,
                title="AI roadmap consulting guide",
                slug="ai-roadmap-consulting-guide",
                content_type=ContentType.HOW_TO,
                status="draft",
                word_count=1500,
                file_path=str(tmp_path / "article.md"),
            ),
            "# Draft body",
        )
        keyword_id = keyword.id

    dashboard = load_dashboard(settings)
    keywords = load_keywords(settings)
    clusters = load_keyword_clusters(settings)
    detail = load_keyword_detail(settings, keyword_id)

    assert dashboard["summary"]["total_keywords"] == 1
    assert dashboard["summary"]["articles"] == 1
    assert dashboard["keywords"][0]["term"] == "ai roadmap consulting"
    assert keywords.keywords[0].term == "ai roadmap consulting"
    assert clusters.clusters[0].cluster_name == "ai"
    assert clusters.clusters[0].keyword_terms == ["ai roadmap consulting"]
    assert detail is not None
    assert detail.keyword.term == "ai roadmap consulting"
    assert detail.serp is not None
    assert detail.serp.competition.competition_level == "medium"
    assert detail.brief is not None
    assert detail.brief.title == "AI roadmap consulting guide"
    assert detail.articles[0].content_preview == "# Draft body"
    assert len(detail.competitors) == 1


def test_keyword_detail_returns_none_for_missing_id(tmp_path: Path):
    settings = _settings(tmp_path)

    detail = load_keyword_detail(settings, "missing")

    assert detail is None


def test_status_payload_reflects_runtime_settings(tmp_path: Path):
    settings = _settings(tmp_path)

    payload = load_status(settings)

    assert payload.active_profile == "default"
    assert payload.environment == settings.app_env
    assert payload.database_url == settings.database_url
    assert payload.site_config_path.endswith("data/site_config.json")
    assert payload.gemini_configured == settings.gemini_ready
    assert payload.serpapi_configured == settings.serpapi_ready
