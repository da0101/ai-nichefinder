import asyncio
from datetime import datetime, timezone

from typer import Argument, Option, Typer
from typing import Annotated

from nichefinder_cli.commands.root import shared
from nichefinder_cli.runtime import build_services, get_runtime
from nichefinder_cli.workflows import generate_brief, rewrite_article, write_article
from nichefinder_db import SeoRepository


def register_content_commands(app: Typer) -> None:
    app.command("brief")(brief)
    app.command("write")(write)
    app.command("rewrite")(rewrite)
    app.command("publish")(publish)


def brief(
    keyword_id: str = Argument(..., help="Keyword ID"),
    force: Annotated[bool, Option("--force", help="Generate brief even if score/rankable gate says no")] = False,
) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(generate_brief(keyword_id, site_config.model_dump(), services, repository, force=force))
        shared.console().print(output.model_dump())
        shared.record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


def write(
    keyword_id: str = Argument(..., help="Keyword ID"),
    force: Annotated[bool, Option("--force", help="Write article even if score/rankable gate says no")] = False,
) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(write_article(keyword_id, site_config.model_dump(), services, repository, force=force))
        shared.console().print(output.model_dump())
        shared.record_gemini_usage(repository, services)


def rewrite(url: str = Argument(..., help="Published URL to rewrite")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(rewrite_article(url, site_config.model_dump(), services, repository))
        shared.console().print(output.model_dump())
        shared.record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


def publish(article_id: str = Argument(...), url: str = Argument(...)) -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.get_article(article_id)
        if article is None:
            raise SystemExit(f"Article not found: {article_id}")
        if article.status != "approved":
            raise SystemExit(f"Article '{article.title}' must be approved before it can be published.")
        article = repository.update_article(
            article_id,
            status="published",
            published_at=datetime.now(timezone.utc),
            published_url=url,
        )
        shared.console().print(f"[green]Published[/green] {article.title} -> {url}")
