from rich.table import Table
from typer import Typer

from nichefinder_cli.commands.root import shared
from nichefinder_cli.runtime import get_runtime
from nichefinder_db import SeoRepository


def register_reporting_commands(app: Typer) -> None:
    app.command("report")(report)
    app.command("budget")(budget)


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
        shared.console().print(table)
        shared.console().print(
            {
                "total_keywords": len(repository.list_keywords()),
                "articles": len(repository.list_articles()),
                "published_articles": len(repository.get_published_articles()),
                "content_performance": repository.get_content_performance_by_type(),
            }
        )


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
        for provider in ["serpapi", "tavily", "ddgs", "bing", "yahoo", "gemini"]:
            usage = repository.get_api_usage(provider)
            table.add_row(
                provider,
                str(usage.call_count if usage else 0),
                f"${usage.spend_usd:.2f}" if usage else "$0.00",
                str(usage.tokens_in if usage else 0),
                str(usage.tokens_out if usage else 0),
            )
        shared.console().print(table)
