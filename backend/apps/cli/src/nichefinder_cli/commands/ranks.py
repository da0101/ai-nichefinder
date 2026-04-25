import asyncio

from rich.console import Console
from rich.table import Table
from typer import Typer

from nichefinder_cli.runtime import build_services, get_runtime
from nichefinder_cli.workflows import check_rankings as check_rankings_workflow
from nichefinder_db import SeoRepository

ranks_app = Typer(help="Rank tracking workflows.")


@ranks_app.command("check")
def check_rankings() -> None:
    settings, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        rows = asyncio.run(check_rankings_workflow(services, repository))
        table = Table(title="Ranking Progress")
        table.add_column("Article")
        table.add_column("Keyword")
        table.add_column("Last Position")
        table.add_column("Current")
        table.add_column("Change")
        for row in rows:
            last_position = row["last"].position if row["last"] else None
            current_position = row["snapshot"].position
            change = "-"
            if last_position and current_position:
                change = f"{last_position - current_position:+d}"
            table.add_row(
                row["article"].title,
                row["keyword"].term,
                str(last_position or "-"),
                str(current_position or "-"),
                change,
            )
        Console().print(table)


@ranks_app.command("sync")
def sync_rankings() -> None:
    check_rankings()
