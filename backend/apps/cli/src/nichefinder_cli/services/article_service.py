from datetime import datetime, timezone

from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository

from nichefinder_cli.viewer_api_models import ArticleMutationDetail, ArticleMutationResponse

from .runtime_context import session_runtime


def approve_article_action(
    *,
    profile_slug: str | None = None,
    article_id: str,
    settings_override: Settings | None = None,
) -> ArticleMutationResponse:
    if not article_id.strip():
        raise ValueError("article_id is required")
    slug, _, _, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.update_article(
            article_id.strip(),
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )
        keyword = repository.get_keyword(article.keyword_id)
    return ArticleMutationResponse(
        profile=slug,
        article=ArticleMutationDetail(
            id=article.id,
            title=article.title,
            status=article.status,
            keyword_term=keyword.term if keyword else None,
            approved_at=article.approved_at.isoformat() if article.approved_at else None,
        ),
    )


def publish_article_action(
    *,
    profile_slug: str | None = None,
    article_id: str,
    url: str,
    settings_override: Settings | None = None,
) -> ArticleMutationResponse:
    if not article_id.strip():
        raise ValueError("article_id is required")
    if not url.strip():
        raise ValueError("url is required")
    slug, _, _, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.get_article(article_id.strip())
        if article is None:
            raise ValueError(f"Article not found: {article_id.strip()}")
        if article.status != "approved":
            raise ValueError(f"Article '{article.title}' must be approved before it can be published.")
        article = repository.update_article(
            article_id.strip(),
            status="published",
            published_at=datetime.now(timezone.utc),
            published_url=url.strip(),
        )
        keyword = repository.get_keyword(article.keyword_id)
    return ArticleMutationResponse(
        profile=slug,
        article=ArticleMutationDetail(
            id=article.id,
            title=article.title,
            status=article.status,
            keyword_term=keyword.term if keyword else None,
            published_url=article.published_url,
            published_at=article.published_at.isoformat() if article.published_at else None,
        ),
    )
