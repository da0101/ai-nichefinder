from datetime import date, timedelta

import typer
from rich.console import Console
from rich.table import Table
from typer import Option, Typer

from nichefinder_cli.runtime import get_runtime
from nichefinder_core.sources.gsc_client import GscClient
from nichefinder_db import SeoRepository

monitor_app = Typer(help="Monitoring and GSC sync commands.")


@monitor_app.command("sync")
def sync(
    days: int = Option(7, "--days", "-d", help="Number of days to sync (counting back from 2 days ago)."),
    property_url: str | None = Option(None, "--property", "-p", help="GSC property URL (default from settings)."),
) -> None:
    settings, _, session_context = get_runtime()

    if not settings.gsc_credentials_path:
        typer.echo(
            "GSC_CREDENTIALS_PATH is not configured. "
            "Add the path to your service account JSON key in .env.",
            err=True,
        )
        raise typer.Exit(code=1)

    console = Console()
    console.print(f"[bold]Syncing GSC data[/bold] - last {days} days")

    client = GscClient(settings)
    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=days - 1)

    records = client.fetch_records(
        start_date=start_date,
        end_date=end_date,
        property_url=property_url,
    )

    if not records:
        console.print("[yellow]No GSC rows returned for this date range.[/yellow]")
        return

    inserted = 0
    updated = 0
    with session_context as session:
        repo = SeoRepository(session)
        for record in records:
            existing = repo.find_search_console_record(
                record.query, record.page_url, record.snapshot_date, record.property_id
            )
            repo.upsert_search_console_record(record)
            if existing is None:
                inserted += 1
            else:
                updated += 1

    table = Table(title=f"GSC Sync - {start_date} to {end_date}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total rows fetched", str(len(records)))
    table.add_row("Inserted (new)", str(inserted))
    table.add_row("Updated (refreshed)", str(updated))
    table.add_row("Property", property_url or settings.gsc_property_url)
    console.print(table)
