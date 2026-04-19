import asyncio
from datetime import datetime, timezone

from nichefinder_cli.commands.articles import articles_app
from nichefinder_cli.commands.db import db_app
from nichefinder_cli.commands.keywords import keywords_app
from nichefinder_cli.commands.monitor import monitor_app
from nichefinder_cli.commands.ranks import ranks_app
from nichefinder_cli.commands.status import status
from nichefinder_cli.commands.viewer import view
from nichefinder_cli.runtime import build_services, get_runtime
from nichefinder_cli.workflows import generate_brief, rewrite_article, run_full_pipeline, write_article
from nichefinder_core.agents.serp_agent import SerpAgentInput
from nichefinder_core.models import Keyword
from nichefinder_core.models.site import SiteConfig, save_site_config
from nichefinder_db import SeoRepository
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Typer

app = Typer(
    add_completion=False,
    no_args_is_help=True,
    help="CLI-first personal SEO intelligence for danilulmashev.com.",
)

app.command()(status)
app.command()(view)
app.add_typer(db_app, name="db")
app.add_typer(keywords_app, name="keywords")
app.add_typer(articles_app, name="articles")
app.add_typer(ranks_app, name="rank")
app.add_typer(monitor_app, name="monitor")


def _console() -> Console:
    return Console()


def _record_gemini_usage(repository: SeoRepository, services) -> None:
    usage = services.gemini.get_usage_stats()
    repository.record_api_usage(
        provider="gemini",
        tokens_in=usage["prompt_tokens"],
        tokens_out=usage["response_tokens"],
    )


@app.command("research")
def research(keyword: str = Argument(..., help="Seed keyword")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        result = asyncio.run(run_full_pipeline(keyword, site_config.model_dump(), services, repository))
        table = Table(title=f"Opportunity Report: {keyword}")
        table.add_column("Keyword ID")
        table.add_column("Keyword")
        table.add_column("Score")
        table.add_column("Priority")
        for item in result["analyses"][:10]:
            opp = item["synthesis"].opportunity_score
            table.add_row(opp.keyword_id, opp.keyword_term, str(opp.composite_score), opp.priority)
        _console().print(table)
        for item in result["analyses"]:
            opp = item["synthesis"].opportunity_score
            if item["synthesis"].should_create_content and Confirm.ask(
                f"Create content for '{opp.keyword_term}'?",
                default=False,
            ):
                output = asyncio.run(write_article(opp.keyword_id, site_config.model_dump(), services, repository))
                _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


@app.command("research-batch")
def research_batch() -> None:
    _, site_config, _ = get_runtime()
    if not site_config.seed_keywords:
        raise SystemExit("No seed_keywords configured in data/site_config.json")
    for seed in site_config.seed_keywords:
        research(seed)


@app.command("serp")
def serp(keyword: str = Argument(..., help="Keyword to analyze")) -> None:
    settings, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        stored = repository.upsert_keyword(
            Keyword(term=keyword, seed_keyword=keyword, source="manual")
        )
        output = asyncio.run(
            services.serp_agent.run(SerpAgentInput(keyword_id=stored.id, keyword_term=stored.term))
        )
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)


@app.command("brief")
def brief(keyword_id: str = Argument(..., help="Keyword ID")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(generate_brief(keyword_id, site_config.model_dump(), services, repository))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


@app.command("write")
def write(keyword_id: str = Argument(..., help="Keyword ID")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(write_article(keyword_id, site_config.model_dump(), services, repository))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)


@app.command("rewrite")
def rewrite(url: str = Argument(..., help="Published URL to rewrite")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        output = asyncio.run(rewrite_article(url, site_config.model_dump(), services, repository))
        _console().print(output.model_dump())
        _record_gemini_usage(repository, services)
        asyncio.run(services.scraper.close())


@app.command("publish")
def publish(article_id: str = Argument(...), url: str = Argument(...)) -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.get_article(article_id)
        if article is None:
            raise SystemExit(f"Article not found: {article_id}")
        if article.status != "approved":
            raise SystemExit(
                f"Article '{article.title}' must be approved before it can be published."
            )
        article = repository.update_article(
            article_id,
            status="published",
            published_at=datetime.now(timezone.utc),
            published_url=url,
        )
        _console().print(f"[green]Published[/green] {article.title} -> {url}")


@app.command("report")
def report() -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        top_keywords = repository.get_top_opportunities(limit=10)
        table = Table(title="Opportunity Report")
        table.add_column("Keyword")
        table.add_column("Score")
        table.add_column("Volume")
        table.add_column("Difficulty")
        for keyword in top_keywords:
            table.add_row(
                keyword.term,
                str(keyword.opportunity_score or "-"),
                str(keyword.monthly_volume or "-"),
                str(keyword.difficulty_score or "-"),
            )
        _console().print(table)
        _console().print(
            {
                "total_keywords": len(repository.list_keywords()),
                "articles": len(repository.list_articles()),
                "published_articles": len(repository.get_published_articles()),
                "content_performance": repository.get_content_performance_by_type(),
            }
        )


@app.command("budget")
def budget() -> None:
    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        table = Table(title="API Budget")
        table.add_column("Provider")
        table.add_column("Calls")
        table.add_column("Spend")
        table.add_column("Tokens In")
        table.add_column("Tokens Out")
        for provider in ["serpapi", "gemini"]:
            usage = repository.get_api_usage(provider)
            table.add_row(
                provider,
                str(usage.call_count if usage else 0),
                f"${usage.spend_usd:.2f}" if usage else "$0.00",
                str(usage.tokens_in if usage else 0),
                str(usage.tokens_out if usage else 0),
            )
        _console().print(table)


@app.command("config")
def config() -> None:
    settings, site_config, _ = get_runtime()
    updated = SiteConfig(
        site_url=Prompt.ask("Site URL", default=site_config.site_url),
        site_name=Prompt.ask("Site name", default=site_config.site_name),
        site_description=Prompt.ask("Site description", default=site_config.site_description),
        target_audience=Prompt.ask("Target audience", default=site_config.target_audience),
        services=[
            item.strip()
            for item in Prompt.ask(
                "Services (comma-separated)",
                default=", ".join(site_config.services),
            ).split(",")
            if item.strip()
        ],
        primary_language=Prompt.ask("Primary language", default=site_config.primary_language),
        blog_url=Prompt.ask("Blog URL", default=site_config.blog_url),
        existing_articles=[
            item.strip()
            for item in Prompt.ask(
                "Existing articles (comma-separated URLs)",
                default=", ".join(site_config.existing_articles),
            ).split(",")
            if item.strip()
        ],
        seed_keywords=[
            item.strip()
            for item in Prompt.ask(
                "Seed keywords (comma-separated)",
                default=", ".join(site_config.seed_keywords),
            ).split(",")
            if item.strip()
        ],
        target_persona=Prompt.ask("Target persona", default=site_config.target_persona),
        competitors=[
            item.strip()
            for item in Prompt.ask(
                "Competitors (comma-separated)",
                default=", ".join(site_config.competitors),
            ).split(",")
            if item.strip()
        ],
        geographic_focus=[
            item.strip()
            for item in Prompt.ask(
                "Geographic focus (comma-separated)",
                default=", ".join(site_config.geographic_focus),
            ).split(",")
            if item.strip()
        ],
    )
    save_site_config(settings.resolved_site_config_path, updated)
    _console().print(f"[green]Updated[/green] {settings.resolved_site_config_path}")
