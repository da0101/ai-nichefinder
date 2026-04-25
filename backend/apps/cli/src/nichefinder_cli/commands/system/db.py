import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from nichefinder_cli.runtime import resolve_runtime_settings
from nichefinder_db import create_db_and_tables
from nichefinder_db.crud import SeoRepository
from nichefinder_db.engine import get_session
from rich.console import Console
from typer import Option, Typer

db_app = Typer(help="Database administration commands.")


def _db_path(settings) -> Path | None:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        raw = url.removeprefix("sqlite:///")
        path = Path(raw)
        return path if path.is_absolute() else Path.cwd() / path
    return None


def _backup_db(settings, console: Console) -> Path | None:
    db_file = _db_path(settings)
    if db_file is None or not db_file.exists() or db_file.stat().st_size == 0:
        return None
    backup_dir = db_file.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    destination = backup_dir / f"seo.db.{stamp}.bak"
    shutil.copy2(db_file, destination)
    console.print(f"[dim]Backed up -> {destination}[/dim]")
    return destination


@db_app.command("init")
def init_db() -> None:
    settings = resolve_runtime_settings()
    console = Console()
    _backup_db(settings, console)
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
    console.print(f"[green]Database schema created[/green] at {settings.database_url}")


@db_app.command("backup")
def backup_db() -> None:
    settings = resolve_runtime_settings()
    console = Console()
    destination = _backup_db(settings, console)
    if destination:
        console.print(f"[green]Backup saved[/green] -> {destination}")
    else:
        console.print("[yellow]Nothing to back up - DB file is empty or not a local SQLite file.[/yellow]")


@db_app.command("export")
def export_db() -> None:
    settings = resolve_runtime_settings()
    console = Console()
    exports_dir = settings.resolve_path(Path("data/exports"))
    exports_dir.mkdir(parents=True, exist_ok=True)

    with get_session(settings) as session:
        repo = SeoRepository(session)
        keywords = repo.list_keywords()
        articles = repo.list_articles()

        payload = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "keywords": [
                {
                    "id": keyword.id,
                    "term": keyword.term,
                    "seed_keyword": keyword.seed_keyword,
                    "source": keyword.source,
                    "search_intent": keyword.search_intent.value if keyword.search_intent else None,
                    "trend_direction": keyword.trend_direction,
                    "opportunity_score": keyword.opportunity_score,
                    "monthly_volume": keyword.monthly_volume,
                    "difficulty_score": keyword.difficulty_score,
                    "lifecycle_status": keyword.lifecycle_status,
                    "discovered_at": keyword.discovered_at.isoformat() if keyword.discovered_at else None,
                }
                for keyword in keywords
            ],
            "articles": [
                {
                    "id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "slug": article.slug,
                    "word_count": article.word_count,
                    "file_path": article.file_path,
                    "published_url": article.published_url,
                    "created_at": article.created_at.isoformat() if article.created_at else None,
                }
                for article in articles
            ],
        }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_path = exports_dir / f"export-{stamp}.json"
    output_path.write_text(json.dumps(payload, indent=2))
    console.print(
        f"[green]Exported[/green] {len(keywords)} keywords + {len(articles)} articles -> {output_path}"
    )


@db_app.command("reset")
def reset_db(
    all_state: bool = Option(
        False,
        "--all-state",
        help="Also remove cached validation/training state and generated outputs for the active profile.",
    ),
) -> None:
    settings = resolve_runtime_settings()
    console = Console()
    db_file = _db_path(settings)

    if db_file is not None:
        for path in (
            db_file,
            db_file.with_suffix(f"{db_file.suffix}-shm"),
            db_file.with_suffix(f"{db_file.suffix}-wal"),
        ):
            if path.exists():
                path.unlink()

    if all_state:
        for path in (settings.resolved_cache_dir, settings.resolve_path(settings.outputs_dir)):
            if path.exists():
                shutil.rmtree(path)

    create_db_and_tables(settings)
    console.print(f"[green]Reset[/green] DB at {settings.database_url}")
    if all_state:
        console.print(
            f"[green]Cleared[/green] cache at {settings.resolved_cache_dir} and outputs at "
            f"{settings.resolve_path(settings.outputs_dir)}"
        )
