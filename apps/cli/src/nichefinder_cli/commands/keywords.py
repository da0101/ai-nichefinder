from nichefinder_core.models.keyword import KeywordSeed
from nichefinder_core.settings import get_settings
from rich.console import Console
from typer import Argument, Option, Typer

keywords_app = Typer(help="Keyword discovery and enrichment workflows.")


@keywords_app.command("discover")
def discover(
    phrase: str = Argument(..., help="Seed phrase to expand."),
    language: str | None = Option(None, "--language", "-l", help="Language override."),
    market: str | None = Option(None, "--market", "-m", help="Market override."),
) -> None:
    """Prepare a keyword discovery request for the current locale profile."""
    settings = get_settings()
    seed = KeywordSeed(
        phrase=phrase,
        language=language or settings.primary_language,
        market=market or settings.primary_market,
    )

    Console().print(
        "[yellow]Discovery adapters are not wired yet.[/yellow]\n"
        f"Prepared request: phrase={seed.phrase!r}, "
        f"language={seed.language!r}, market={seed.market!r}"
    )

