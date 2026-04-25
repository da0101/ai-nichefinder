from rich.console import Console
from typer import Typer

briefs_app = Typer(help="Compatibility wrapper for brief workflows.")


@briefs_app.command("generate")
def generate_placeholder() -> None:
    Console().print("[yellow]Use `seo brief <keyword-id>` for the new brief workflow.[/yellow]")
