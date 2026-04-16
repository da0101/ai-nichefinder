from rich.console import Console
from typer import Typer

ranks_app = Typer(help="Rank tracking and Search Console workflows.")


@ranks_app.command("sync")
def sync_placeholder() -> None:
    """Placeholder for Phase 6 rank synchronization."""
    Console().print(
        "[yellow]Rank tracking is scaffolded but not implemented yet.[/yellow]"
    )

