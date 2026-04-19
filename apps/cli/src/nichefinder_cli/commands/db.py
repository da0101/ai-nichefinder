from nichefinder_core.settings import get_settings
from nichefinder_db import create_db_and_tables
from rich.console import Console
from typer import Typer

db_app = Typer(help="Database administration commands.")


@db_app.command("init")
def init_db() -> None:
    """Create database tables from SQLModel metadata."""
    settings = get_settings()
    try:
        create_db_and_tables(settings)
    except ModuleNotFoundError as exc:
        if exc.name == "psycopg":
            raise SystemExit(
                "Current NICHEFINDER_DB_URL points to PostgreSQL, but the project now defaults "
                "to SQLite. Update `.env` to `sqlite:///data/db/seo.db` or override "
                "`NICHEFINDER_DB_URL` before running `seo db init`."
            ) from exc
        raise
    Console().print(
        f"[green]Database schema created[/green] at {settings.database_url}"
    )
