from nichefinder_core.models.site import load_site_config
from nichefinder_core.settings import get_settings
from rich.console import Console
from rich.table import Table


def status() -> None:
    settings = get_settings()
    site_config = load_site_config(settings.resolved_site_config_path) if settings.resolved_site_config_path.exists() else None
    console = Console()

    table = Table(title="Personal SEO Tool Status")
    table.add_column("Item")
    table.add_column("Value")

    table.add_row("Environment", settings.app_env)
    table.add_row("Database URL", settings.database_url)
    table.add_row("Site config", str(settings.resolved_site_config_path))
    table.add_row("Articles dir", str(settings.resolved_articles_dir))
    table.add_row("Reports dir", str(settings.resolved_reports_dir))
    table.add_row("Site URL", site_config.site_url if site_config else settings.site_url)
    table.add_row("Primary language", site_config.primary_language if site_config else settings.primary_language)
    table.add_row("Cache dir", str(settings.resolved_cache_dir))
    table.add_row("Gemini configured", settings.flag(settings.gemini_ready))
    table.add_row("SerpAPI configured", settings.flag(settings.serpapi_ready))

    console.print(table)
