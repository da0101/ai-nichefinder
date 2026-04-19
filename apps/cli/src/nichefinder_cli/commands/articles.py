from datetime import datetime, timezone

from rich.console import Console
from rich.table import Table
from typer import Argument, Typer

from nichefinder_db import SeoRepository

articles_app = Typer(help="Generated article workflows.")


@articles_app.command("list")
def list_articles() -> None:
    from nichefinder_cli.runtime import get_runtime

    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        table = Table(title="Articles")
        table.add_column("ID")
        table.add_column("Title")
        table.add_column("Status")
        table.add_column("Keyword")
        for article in repository.list_articles():
            keyword = repository.get_keyword(article.keyword_id)
            table.add_row(article.id, article.title, article.status, keyword.term if keyword else "-")
        Console().print(table)


@articles_app.command("approve")
def approve_article(article_id: str = Argument(..., help="Article ID")) -> None:
    from nichefinder_cli.runtime import get_runtime

    _, _, session_context = get_runtime()
    with session_context as session:
        repository = SeoRepository(session)
        article = repository.update_article(
            article_id,
            status="approved",
            approved_at=datetime.now(timezone.utc),
        )
        Console().print(f"[green]Approved[/green] {article.title}")
