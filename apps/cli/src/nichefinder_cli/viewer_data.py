import json
from datetime import date, datetime

from sqlmodel import select

from nichefinder_core.models import (
    ApiUsageRecord,
    Article,
    ArticleVersion,
    Keyword,
)
from nichefinder_core.settings import Settings
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


def load_keyword_detail(settings: Settings, keyword_id: str) -> dict | None:
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
        return {
            "keyword": {
                "id": keyword.id,
                "term": keyword.term,
                "seed_keyword": keyword.seed_keyword,
                "source": keyword.source,
                "intent": keyword.search_intent.value if keyword.search_intent else None,
                "trend": keyword.trend_direction,
                "score": keyword.opportunity_score,
                "volume": keyword.monthly_volume,
                "difficulty": keyword.difficulty_score,
                "discovered_at": _stamp(keyword.discovered_at),
            },
            "serp": None
            if serp_result is None
            else {
                "fetched_at": _stamp(serp_result.fetched_at),
                "competition": _json_loads(serp_result.competition_analysis, {}),
                "pages": _json_loads(serp_result.pages_json, [])[:10],
            },
            "competitors": [
                {
                    "title": page.title,
                    "url": page.url,
                    "word_count": page.word_count,
                    "reading_time_min": page.estimated_reading_time_min,
                    "summary": page.content_summary,
                }
                for page in competitor_pages
            ],
            "brief": None
            if brief is None
            else {
                "title": brief.suggested_title,
                "content_type": brief.content_type.value,
                "tone": brief.tone,
                "word_count_target": brief.word_count_target,
                "secondary_keywords": brief.secondary_keywords,
                "suggested_h2_structure": brief.suggested_h2_structure,
                "questions_to_answer": brief.questions_to_answer,
            },
            "articles": [_article_payload(session, repository, article) for article in articles],
        }


def _article_payload(session, repository: SeoRepository, article: Article) -> dict:
    latest_version = session.exec(
        select(ArticleVersion)
        .where(ArticleVersion.article_id == article.id)
        .order_by(ArticleVersion.created_at.desc())
    ).first()
    latest_rank = repository.get_latest_ranking_snapshot(article.id)
    return {
        "id": article.id,
        "title": article.title,
        "status": article.status,
        "slug": article.slug,
        "word_count": article.word_count,
        "file_path": article.file_path,
        "published_url": article.published_url,
        "created_at": _stamp(article.created_at),
        "latest_rank_position": latest_rank.position if latest_rank else None,
        "content_preview": (latest_version.content[:4000] if latest_version else None),
    }
