import asyncio

from nichefinder_cli.free_validation import run_free_validation_pipeline
from nichefinder_cli.runtime import (
    build_services,
    create_profile,
    delete_profile,
    get_active_profile,
    get_runtime,
    resolve_runtime_settings,
    save_profile_site_config,
)
from nichefinder_cli.workflows import run_full_pipeline
from nichefinder_core.models.site import SiteConfig
from nichefinder_db import SeoRepository


def create_profile_action(*, slug: str, from_current: bool = False, use: bool = False, payload: dict | None = None) -> dict:
    if not slug.strip():
        raise ValueError("slug is required")
    if payload is not None:
        source_site_config = SiteConfig.model_validate(payload)
    else:
        source_site_config = get_runtime()[1] if from_current else SiteConfig()
    normalized_slug, _ = create_profile(slug, site_config=source_site_config, use=use)
    target_settings = get_runtime(normalized_slug)[0]
    return {
        "slug": normalized_slug,
        "site_config": source_site_config.model_dump(),
        "site_config_path": str(target_settings.resolved_site_config_path),
        "database_url": target_settings.database_url,
        "active": use,
    }


def load_profile_config(profile_slug: str | None = None) -> dict:
    slug, settings, site_config = _profile_runtime(profile_slug)
    return {
        "profile": slug,
        "site_config": site_config.model_dump(),
        "paths": {
            "site_config_path": str(settings.resolved_site_config_path),
            "database_url": settings.database_url,
        },
    }


def save_profile_config_action(*, profile_slug: str | None = None, payload: dict) -> dict:
    slug, _, _ = _profile_runtime(profile_slug)
    config = SiteConfig.model_validate(payload)
    save_profile_site_config(slug, config)
    return load_profile_config(slug)


def delete_profile_action(*, profile_slug: str) -> dict:
    slug, _, _ = _profile_runtime(profile_slug)
    delete_profile(slug)
    active = get_active_profile() or "default"
    return {"deleted": slug, "active_profile": active}


def run_validate_free_action(
    *,
    profile_slug: str | None = None,
    keyword: str,
    sources: tuple[str, ...] = ("ddgs", "bing", "yahoo"),
) -> dict:
    if not keyword.strip():
        raise ValueError("keyword is required")
    slug, settings, site_config = _profile_runtime(profile_slug)
    _, _, session_context = get_runtime(slug)
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        try:
            result = asyncio.run(
                run_free_validation_pipeline(
                    keyword,
                    site_config.model_dump(),
                    services,
                    repository,
                    location=settings.search_location,
                    sources=sources,
                    console=None,
                )
            )
            usage = services.gemini.get_usage_stats()
            repository.record_api_usage(
                provider="gemini",
                tokens_in=usage["prompt_tokens"],
                tokens_out=usage["response_tokens"],
            )
        finally:
            asyncio.run(services.scraper.close())
    return {
        "profile": slug,
        "keyword": keyword,
        "sources": list(sources),
        "location": settings.search_location,
        "buyer_problems": [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in getattr(result.get("keyword_output"), "buyer_problems", [])
        ],
        "shortlist": [
            {
                "term": item.term,
                "score": item.score,
                "selected": item.selected,
                "notes": item.notes,
                "breakdown": item.breakdown,
            }
            for item in result.get("shortlist", [])
        ],
        "keyword_validations": [_validation_payload(item) for item in result.get("keyword_validations", [])],
        "problem_validations": [_validation_payload(item) for item in result.get("problem_validations", [])],
        "article_evidence": [
            {
                "query": item.query,
                "source": item.source,
                "validation_score": item.validation_score,
                "source_urls": item.source_urls,
                "pages_scraped": item.pages_scraped,
                "recurring_headings": item.recurring_headings,
                "body_signal_terms": item.body_signal_terms,
                "question_bank": item.question_bank,
                "suggested_secondary_keywords": item.suggested_secondary_keywords,
            }
            for item in result.get("article_evidence", [])
        ],
    }


def run_research_action(*, profile_slug: str | None = None, keyword: str) -> dict:
    if not keyword.strip():
        raise ValueError("keyword is required")
    slug, settings, site_config = _profile_runtime(profile_slug)
    _, _, session_context = get_runtime(slug)
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        try:
            result = asyncio.run(
                run_full_pipeline(
                    keyword.strip(),
                    site_config.model_dump(),
                    services,
                    repository,
                    location=settings.search_location,
                    console=None,
                )
            )
            usage = services.gemini.get_usage_stats()
            repository.record_api_usage(
                provider="gemini",
                tokens_in=usage["prompt_tokens"],
                tokens_out=usage["response_tokens"],
            )
        finally:
            asyncio.run(services.scraper.close())
    analyses = result.get("analyses", [])
    return {
        "profile": slug,
        "keyword": keyword.strip(),
        "location": settings.search_location,
        "keywords_found": result["keyword_output"].keywords_found,
        "keywords_saved": result["keyword_output"].keywords_saved,
        "keyword_ids": result["keyword_output"].keyword_ids,
        "buyer_problems": [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in getattr(result["keyword_output"], "buyer_problems", [])
        ],
        "analyses": [_analysis_payload(item) for item in analyses],
    }


def _validation_payload(item) -> dict:
    return {
        "source": item.source,
        "query": item.query,
        "score": item.score,
        "degraded": item.degraded,
        "unavailable": getattr(item, "unavailable", False),
        "result_count": item.result_count,
        "top_domains": item.top_domains,
        "notes": item.notes,
    }


def _analysis_payload(item: dict) -> dict:
    synthesis = item["synthesis"]
    opportunity = synthesis.opportunity_score
    keyword = item["keyword"]
    serp = item["serp"]
    trend = item["trend"]
    return {
        "keyword": {
            "id": keyword.id,
            "term": keyword.term,
            "intent": keyword.search_intent.value if keyword.search_intent else None,
        },
        "opportunity": opportunity.model_dump(),
        "should_create_content": synthesis.should_create_content,
        "content_angle": synthesis.content_angle,
        "serp": serp.model_dump(),
        "trend": trend.model_dump(),
        "ads": item["ads"].model_dump(),
        "competitor": item["competitor"],
    }


def _profile_runtime(profile_slug: str | None) -> tuple[str, object, SiteConfig]:
    if profile_slug in (None, ""):
        slug = get_active_profile(resolve_runtime_settings()) or "default"
    elif profile_slug == "default":
        slug = "default"
    else:
        slug = profile_slug
    settings, site_config, _ = get_runtime(slug)
    return slug, settings, site_config
