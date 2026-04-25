import asyncio

from rich.table import Table
from typer import Argument, Typer

from nichefinder_cli.commands.root import shared
from nichefinder_cli.runtime import build_services, get_runtime
from nichefinder_cli.workflows import run_full_pipeline
from nichefinder_core.agents.serp_agent import SerpAgentInput
from nichefinder_core.models import Keyword
from nichefinder_db import SeoRepository


def register_research_commands(app: Typer) -> None:
    app.command("research")(research)
    app.command("research-batch")(research_batch)
    app.command("serp")(serp)
    app.command("validate-free")(validate_free)
    app.command("validate-ddgs")(validate_ddgs)
    app.command("validate-bing")(validate_bing)
    app.command("validate-yahoo")(validate_yahoo)


def research(keyword: str = Argument(..., help="Seed keyword")) -> None:
    settings, site_config, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        result = asyncio.run(
            run_full_pipeline(
                keyword,
                site_config.model_dump(),
                services,
                repository,
                location=settings.search_location,
                console=shared.console(),
            )
        )
        table = Table(title=f"Opportunity Report: {keyword}")
        table.add_column("Keyword ID")
        table.add_column("Keyword")
        table.add_column("Score")
        table.add_column("Priority")
        for item in result["analyses"][:10]:
            opportunity = item["synthesis"].opportunity_score
            table.add_row(
                opportunity.keyword_id,
                opportunity.keyword_term,
                str(opportunity.composite_score),
                opportunity.priority,
            )
        shared.console().print(table)
        shared.record_gemini_usage(repository, services)
        shared.print_serpapi_usage(repository, settings)
        shared.print_tavily_usage(repository, settings)
        shared.print_ddgs_usage(repository, settings)
        shared.print_bing_usage(repository, settings)
        shared.print_yahoo_usage(repository, settings)
        asyncio.run(services.scraper.close())


def research_batch() -> None:
    _, site_config, _ = get_runtime()
    if not site_config.seed_keywords:
        raise SystemExit("No seed_keywords configured in data/site_config.json")
    for seed in site_config.seed_keywords:
        research(seed)


def serp(keyword: str = Argument(..., help="Keyword to analyze")) -> None:
    settings, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        stored = repository.upsert_keyword(Keyword(term=keyword, seed_keyword=keyword, source="manual"))
        output = asyncio.run(
            services.serp_agent.run(SerpAgentInput(keyword_id=stored.id, keyword_term=stored.term))
        )
        shared.console().print(output.model_dump())
        shared.record_gemini_usage(repository, services)


def validate_free(keyword: str = Argument(..., help="Seed keyword")) -> None:
    shared.run_free_validation_command(keyword, sources=("ddgs", "bing", "yahoo"))


def validate_ddgs(keyword: str = Argument(..., help="Seed keyword")) -> None:
    shared.run_free_validation_command(keyword, sources=("ddgs",))


def validate_bing(keyword: str = Argument(..., help="Seed keyword")) -> None:
    shared.run_free_validation_command(keyword, sources=("bing",))


def validate_yahoo(keyword: str = Argument(..., help="Seed keyword")) -> None:
    shared.run_free_validation_command(keyword, sources=("yahoo",))
