import asyncio
from contextlib import contextmanager

from nichefinder_cli.free_validation import run_free_validation_pipeline
from nichefinder_cli.workflows import run_full_pipeline
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository

from .runtime_context import session_runtime
from .workflow_support import analysis_payload, record_gemini_usage, validation_payload
from nichefinder_cli.runtime import build_services


@contextmanager
def _services_context(settings, repository: SeoRepository):
    services = build_services(settings, repository)
    try:
        yield services
    finally:
        asyncio.run(services.scraper.close())


def run_validate_free_action(
    *,
    profile_slug: str | None = None,
    keyword: str,
    sources: tuple[str, ...] = ("ddgs", "bing", "yahoo"),
    settings_override: Settings | None = None,
) -> dict:
    if not keyword.strip():
        raise ValueError("keyword is required")
    slug, settings, site_config, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        with _services_context(settings, repository) as services:
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
            record_gemini_usage(repository, services)
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
        "keyword_validations": [validation_payload(item) for item in result.get("keyword_validations", [])],
        "problem_validations": [validation_payload(item) for item in result.get("problem_validations", [])],
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


def run_research_action(
    *,
    profile_slug: str | None = None,
    keyword: str,
    settings_override: Settings | None = None,
) -> dict:
    if not keyword.strip():
        raise ValueError("keyword is required")
    slug, settings, site_config, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        with _services_context(settings, repository) as services:
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
            record_gemini_usage(repository, services)
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
        "analyses": [analysis_payload(item) for item in analyses],
    }
