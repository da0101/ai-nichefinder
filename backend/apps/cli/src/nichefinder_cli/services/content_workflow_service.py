import asyncio
from contextlib import contextmanager

from nichefinder_cli.workflows import generate_brief, rewrite_article, write_article
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository

from nichefinder_cli.runtime import build_services
from nichefinder_cli.viewer_api_models import RewriteJobResponse

from .runtime_context import session_runtime
from .workflow_support import record_gemini_usage


@contextmanager
def _services_context(settings, repository: SeoRepository):
    services = build_services(settings, repository)
    try:
        yield services
    finally:
        asyncio.run(services.scraper.close())


def run_generate_brief_action(
    *,
    profile_slug: str | None = None,
    keyword_id: str,
    force: bool = False,
    settings_override: Settings | None = None,
) -> dict:
    if not keyword_id.strip():
        raise ValueError("keyword_id is required")
    slug, settings, site_config, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        with _services_context(settings, repository) as services:
            output = asyncio.run(
                generate_brief(
                    keyword_id.strip(),
                    site_config.model_dump(),
                    services,
                    repository,
                    force=force,
                )
            )
            record_gemini_usage(repository, services)
    return {
        "profile": slug,
        "keyword_id": keyword_id.strip(),
        "force": force,
        "brief": output.model_dump(),
    }


def run_write_article_action(
    *,
    profile_slug: str | None = None,
    keyword_id: str,
    force: bool = False,
    settings_override: Settings | None = None,
) -> dict:
    if not keyword_id.strip():
        raise ValueError("keyword_id is required")
    slug, settings, site_config, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        with _services_context(settings, repository) as services:
            output = asyncio.run(
                write_article(
                    keyword_id.strip(),
                    site_config.model_dump(),
                    services,
                    repository,
                    force=force,
                )
            )
            record_gemini_usage(repository, services)
    return {
        "profile": slug,
        "keyword_id": keyword_id.strip(),
        "force": force,
        "article": output.model_dump(),
    }


def run_rewrite_article_action(
    *,
    profile_slug: str | None = None,
    url: str,
    settings_override: Settings | None = None,
) -> RewriteJobResponse:
    if not url.strip():
        raise ValueError("url is required")
    slug, settings, site_config, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        with _services_context(settings, repository) as services:
            output = asyncio.run(
                rewrite_article(
                    url.strip(),
                    site_config.model_dump(),
                    services,
                    repository,
                )
            )
            record_gemini_usage(repository, services)
    return RewriteJobResponse(
        profile=slug,
        url=url.strip(),
        article=output.model_dump(),
    )
