from nichefinder_core.settings import get_settings
from rich.console import Console
from rich.table import Table


def status() -> None:
    """Show environment, locale defaults, and credential readiness."""
    settings = get_settings()
    console = Console()

    table = Table(title="AI Nichefinder Status")
    table.add_column("Item")
    table.add_column("Value")

    table.add_row("Environment", settings.app_env)
    table.add_row("Primary market", settings.primary_market)
    table.add_row("Primary language", settings.primary_language)
    table.add_row("Secondary language", settings.secondary_language)
    table.add_row("Portfolio URL", settings.portfolio_url or "not set")
    table.add_row("Database URL", settings.database_url)
    table.add_row("Cache dir", str(settings.cache_dir))
    table.add_row("Google Ads configured", settings.flag(settings.google_ads_ready))
    table.add_row("Serper configured", settings.flag(settings.serper_ready))
    table.add_row("Programmable Search configured", settings.flag(settings.programmable_search_ready))
    table.add_row("Search Console configured", settings.flag(settings.search_console_ready))
    table.add_row("Gemini configured", settings.flag(settings.gemini_ready))

    console.print(table)

