import json
from datetime import date, datetime

from sqlmodel import select

from nichefinder_cli.viewer_api_models import (
    ArticleApiModel,
    ArticlesResponse,
    ArticlesSummary,
    BudgetResponse,
    BudgetUsageRow,
    ContentPerformanceRow,
    ReportKeywordRow,
    ReportResponse,
    ReportSummary,
    StatusResponse,
)
from nichefinder_cli.viewer_keyword_api_models import (
    CompetitionAnalysisResponse,
    CompetitorPageResponse,
    ContentBriefResponse,
    KeywordClusterResponse,
    KeywordClustersResponse,
    KeywordDetailResponse,
    KeywordMetadataResponse,
    KeywordsResponse,
    KeywordSummaryApiModel,
    ScoreBreakdownResponse,
    SerpPageResponse,
    SerpResponse,
)
from nichefinder_core.models import (
    ApiUsageRecord,
    Article,
    ArticleVersion,
    Keyword,
)
from nichefinder_core.settings import Settings
from nichefinder_core.models.site import load_site_config
from nichefinder_cli.runtime import get_active_profile
from nichefinder_db import SeoRepository, get_session


def _json_loads(value: str | None, default):
    if not value:
        return default
    return json.loads(value)


def _stamp(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def load_dashboard(settings: Settings) -> dict:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keywords = repository.list_keywords()[:20]
        articles = repository.list_articles()[:20]
        usage_rows = list(session.exec(select(ApiUsageRecord).order_by(ApiUsageRecord.provider)).all())
        return {
            "summary": {
                "total_keywords": len(repository.list_keywords()),
                "briefed_keywords": sum(
                    1 for keyword in repository.list_keywords() if repository.get_latest_content_brief(keyword.id)
                ),
                "articles": len(articles),
                "published_articles": len(repository.get_published_articles()),
            },
            "keywords": [
                {
                    "id": keyword.id,
                    "term": keyword.term,
                    "intent": keyword.search_intent.value if keyword.search_intent else None,
                    "trend": keyword.trend_direction,
                    "score": keyword.opportunity_score,
                    "volume": keyword.monthly_volume,
                    "difficulty": keyword.difficulty_score,
                    "has_brief": repository.get_latest_content_brief(keyword.id) is not None,
                    "priority": (_score_breakdown(repository, keyword.id) or {}).get("priority"),
                }
                for keyword in keywords
            ],
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "file_path": article.file_path,
                    "published_url": article.published_url,
                    "created_at": _stamp(article.created_at),
                }
                for article in articles
            ],
            "usage": [
                {
                    "provider": row.provider,
                    "calls": row.call_count,
                    "spend_usd": row.spend_usd,
                    "tokens_in": row.tokens_in,
                    "tokens_out": row.tokens_out,
                    "usage_month": _stamp(row.usage_month),
                }
                for row in usage_rows
            ],
            "paths": {
                "database": settings.database_url,
                "articles_dir": str(settings.resolved_articles_dir),
            },
        }


def load_status(settings: Settings) -> StatusResponse:
    site_config = _safe_site_config(settings)
    return StatusResponse(
        active_profile=get_active_profile(settings) or "default",
        environment=settings.app_env,
        database_url=settings.database_url,
        site_config_path=str(settings.resolved_site_config_path),
        articles_dir=str(settings.resolved_articles_dir),
        reports_dir=str(settings.resolved_reports_dir),
        cache_dir=str(settings.resolved_cache_dir),
        site_url=site_config.site_url if site_config else settings.site_url,
        primary_language=site_config.primary_language if site_config else settings.primary_language,
        gemini_configured=settings.gemini_ready,
        serpapi_configured=settings.serpapi_ready,
    )


def load_keywords(settings: Settings) -> KeywordsResponse:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        return KeywordsResponse(
            keywords=[
                KeywordSummaryApiModel(
                    id=keyword.id,
                    term=keyword.term,
                    intent=keyword.search_intent.value if keyword.search_intent else None,
                    trend=keyword.trend_direction,
                    score=keyword.opportunity_score,
                    volume=keyword.monthly_volume,
                    difficulty=keyword.difficulty_score,
                    has_brief=repository.get_latest_content_brief(keyword.id) is not None,
                    priority=(_score_breakdown(repository, keyword.id) or {}).get("priority"),
                )
                for keyword in repository.list_keywords()
            ]
        )


def load_keyword_clusters(settings: Settings) -> KeywordClustersResponse:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        groups: dict[str, list[Keyword]] = {}
        for keyword in repository.list_keywords():
            key = keyword.term.split()[0].lower()
            groups.setdefault(key, []).append(keyword)

        clusters = [
            KeywordClusterResponse(
                cluster_name=name,
                total_cluster_volume=sum(item.monthly_volume or 0 for item in group),
                primary_keyword_id=max(group, key=lambda item: item.monthly_volume or 0).id,
                keyword_ids=[item.id for item in group],
                keyword_terms=[item.term for item in group],
            )
            for name, group in groups.items()
        ]
        clusters.sort(key=lambda item: (-item.total_cluster_volume, item.cluster_name))
        return KeywordClustersResponse(clusters=clusters)


def load_articles(settings: Settings) -> ArticlesResponse:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        articles = repository.list_articles()
        return ArticlesResponse(
            articles=[_article_payload(session, repository, article) for article in articles],
            summary=ArticlesSummary(
                total_articles=len(articles),
                published_articles=len(repository.get_published_articles()),
            ),
        )


def load_report(settings: Settings) -> ReportResponse:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        top_keywords = repository.get_top_opportunities(limit=10)
        return ReportResponse(
            top_keywords=[
                ReportKeywordRow(
                    id=keyword.id,
                    term=keyword.term,
                    score=keyword.opportunity_score,
                    volume=keyword.monthly_volume,
                    difficulty=keyword.difficulty_score,
                )
                for keyword in top_keywords
            ],
            summary=ReportSummary(
                total_keywords=len(repository.list_keywords()),
                articles=len(repository.list_articles()),
                published_articles=len(repository.get_published_articles()),
                content_performance=[
                    ContentPerformanceRow.model_validate(row)
                    for row in repository.get_content_performance_by_type()
                ],
            ),
        )


def load_budget(settings: Settings) -> BudgetResponse:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        providers = ["serpapi", "tavily", "ddgs", "bing", "yahoo", "gemini"]
        usage = []
        for provider in providers:
            row = repository.get_api_usage(provider)
            usage.append(
                {
                    "provider": provider,
                    "calls": row.call_count if row else 0,
                    "spend_usd": row.spend_usd if row else 0.0,
                    "tokens_in": row.tokens_in if row else 0,
                    "tokens_out": row.tokens_out if row else 0,
                }
            )
        return BudgetResponse(usage=[BudgetUsageRow.model_validate(row) for row in usage])


def _score_breakdown(repository, keyword_id: str) -> dict | None:
    record = repository.get_latest_opportunity_score(keyword_id)
    if record is None:
        return None
    return {
        "volume": record.volume_score,
        "difficulty": record.difficulty_score,
        "trend": record.trend_score,
        "intent": record.intent_score,
        "competition": record.competition_score,
        "composite": record.composite_score,
        "priority": record.priority,
        "action": record.action,
        "why": record.why_good_fit,
    }


def load_keyword_detail(settings: Settings, keyword_id: str) -> KeywordDetailResponse | None:
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.get_keyword(keyword_id)
        if keyword is None:
            return None

        serp_result = repository.get_latest_serp_result(keyword.id)
        competitor_pages = repository.list_competitor_pages(serp_result.id) if serp_result else []
        brief = repository.get_latest_content_brief(keyword.id)
        articles = list(
            session.exec(
                select(Article).where(Article.keyword_id == keyword.id).order_by(Article.created_at.desc())
            ).all()
        )
        breakdown = _score_breakdown(repository, keyword.id)
        return KeywordDetailResponse(
            keyword=KeywordMetadataResponse(
                id=keyword.id,
                term=keyword.term,
                seed_keyword=keyword.seed_keyword,
                source=keyword.source,
                intent=keyword.search_intent.value if keyword.search_intent else None,
                trend=keyword.trend_direction,
                score=keyword.opportunity_score,
                volume=keyword.monthly_volume,
                difficulty=keyword.difficulty_score,
                discovered_at=_stamp(keyword.discovered_at),
            ),
            score_breakdown=None if breakdown is None else ScoreBreakdownResponse.model_validate(breakdown),
            serp=None
            if serp_result is None
            else SerpResponse(
                fetched_at=_stamp(serp_result.fetched_at),
                competition=CompetitionAnalysisResponse.model_validate(_json_loads(serp_result.competition_analysis, {})),
                pages=[
                    SerpPageResponse.model_validate(page)
                    for page in _json_loads(serp_result.pages_json, [])[:10]
                ],
            ),
            competitors=[
                CompetitorPageResponse(
                    title=page.title,
                    url=page.url,
                    word_count=page.word_count,
                    reading_time_min=page.estimated_reading_time_min,
                    summary=page.content_summary,
                )
                for page in competitor_pages
            ],
            brief=None
            if brief is None
            else ContentBriefResponse(
                title=brief.suggested_title,
                content_type=brief.content_type.value,
                tone=brief.tone,
                word_count_target=brief.word_count_target,
                secondary_keywords=brief.secondary_keywords,
                suggested_h2_structure=brief.suggested_h2_structure,
                questions_to_answer=brief.questions_to_answer,
            ),
            articles=[_article_payload(session, repository, article) for article in articles],
        )


def _article_payload(session, repository: SeoRepository, article: Article) -> ArticleApiModel:
    latest_version = session.exec(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article.id)
        .order_by(ArticleVersion.created_at.desc())
    ).first()
    latest_rank = repository.get_latest_ranking_snapshot(article.id)
    keyword = repository.get_keyword(article.keyword_id)
    return ArticleApiModel(
        id=article.id,
        title=article.title,
        status=article.status,
        keyword_term=keyword.term if keyword else None,
        slug=article.slug,
        word_count=article.word_count,
        file_path=article.file_path,
        published_url=article.published_url,
        created_at=_stamp(article.created_at),
        approved_at=_stamp(article.approved_at),
        published_at=_stamp(article.published_at),
        latest_rank_position=latest_rank.position if latest_rank else None,
        content_preview=(latest_version.content[:4000] if latest_version else None),
    )


def _safe_site_config(settings: Settings):
    if not settings.resolved_site_config_path.exists():
        return None
    try:
        return load_site_config(settings.resolved_site_config_path)
    except Exception:
        return None
