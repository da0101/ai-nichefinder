from nichefinder_core.settings import get_settings
from nichefinder_db.bootstrap import create_schema
from rich.console import Console
from typer import Typer

db_app = Typer(help="Database administration commands.")


@db_app.command("init")
def init_db() -> None:
    """Create database tables from SQLAlchemy metadata."""
    settings = get_settings()
    create_schema(settings)
    Console().print(
        f"[green]Database schema created[/green] at {settings.database_url}"
    )

