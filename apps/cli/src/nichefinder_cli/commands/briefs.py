from rich.console import Console
from typer import Typer

briefs_app = Typer(help="Content brief generation workflows.")


@briefs_app.command("generate")
def generate_placeholder() -> None:
    """Placeholder for Phase 5 Gemini-driven brief generation."""
    Console().print(
        "[yellow]Brief generation is scaffolded but not implemented yet.[/yellow]"
    )

