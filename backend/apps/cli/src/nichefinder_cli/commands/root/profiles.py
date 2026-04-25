from typer import Argument, Option, Typer
from typing import Annotated

from rich.prompt import Prompt
from rich.table import Table

from nichefinder_cli.commands.root import shared
from nichefinder_cli.runtime import (
    create_profile,
    get_active_profile,
    get_runtime,
    list_profiles,
    resolve_runtime_settings,
    save_profile_site_config,
    set_active_profile,
)
from nichefinder_core.models.site import SiteConfig


def register_profile_commands(app: Typer) -> None:
    app.command("profile-list")(profile_list)
    app.command("profile-init")(profile_init)
    app.command("profile-use")(profile_use)
    app.command("profile-status")(profile_status)
    app.command("config")(config)


def profile_list() -> None:
    settings = resolve_runtime_settings()
    active = get_active_profile(settings)
    table = Table(title="Profiles")
    table.add_column("Profile")
    table.add_column("Status")
    profiles = list_profiles(settings)
    if not profiles:
        shared.console().print("[yellow]No profiles yet. Use `uv run seo profile-init <slug>`.[/yellow]")
        return
    for slug in profiles:
        table.add_row(slug, "active" if slug == active else "")
    shared.console().print(table)


def profile_init(
    slug: str = Argument(..., help="Profile slug"),
    from_current: Annotated[bool, Option("--from-current", help="Copy the currently active site config into the new profile")] = False,
    use: Annotated[bool, Option("--use", help="Switch to the new profile after creating it")] = False,
) -> None:
    source_site_config = get_runtime()[1] if from_current else SiteConfig()
    normalized_slug, target_root = create_profile(slug, site_config=source_site_config, use=use)
    shared.console().print(f"[green]Created[/green] profile {normalized_slug} at {target_root}")
    if use:
        shared.console().print(f"[green]Active profile[/green] -> {normalized_slug}")


def profile_use(slug: str = Argument(..., help="Profile slug")) -> None:
    active = set_active_profile(slug)
    shared.console().print(f"[green]Active profile[/green] -> {active}")


def profile_status() -> None:
    settings = resolve_runtime_settings()
    active = get_active_profile(settings)
    if active is None:
        shared.console().print("[dim]Active profile:[/dim] default")
        shared.console().print(f"[dim]Site config:[/dim] {settings.resolved_site_config_path}")
        return
    active_settings = resolve_runtime_settings(active)
    shared.console().print(f"[dim]Active profile:[/dim] {active}")
    shared.console().print(f"[dim]Site config:[/dim] {active_settings.resolved_site_config_path}")
    shared.console().print(f"[dim]DB:[/dim] {active_settings.database_url}")
    shared.console().print(f"[dim]Cache:[/dim] {active_settings.resolved_cache_dir}")


def config() -> None:
    settings, site_config, _ = get_runtime()
    updated = SiteConfig(
        site_url=Prompt.ask("Site URL", default=site_config.site_url),
        site_name=Prompt.ask("Site name", default=site_config.site_name),
        site_description=Prompt.ask("Site description", default=site_config.site_description),
        target_audience=Prompt.ask("Target audience", default=site_config.target_audience),
        services=[
            item.strip()
            for item in Prompt.ask("Services (comma-separated)", default=", ".join(site_config.services)).split(",")
            if item.strip()
        ],
        primary_language=Prompt.ask("Primary language", default=site_config.primary_language),
        blog_url=Prompt.ask("Blog URL", default=site_config.blog_url),
        existing_articles=[
            item.strip()
            for item in Prompt.ask(
                "Existing articles (comma-separated URLs)",
                default=", ".join(site_config.existing_articles),
            ).split(",")
            if item.strip()
        ],
        seed_keywords=[
            item.strip()
            for item in Prompt.ask("Seed keywords (comma-separated)", default=", ".join(site_config.seed_keywords)).split(",")
            if item.strip()
        ],
        target_persona=Prompt.ask("Target persona", default=site_config.target_persona),
        competitors=[
            item.strip()
            for item in Prompt.ask("Competitors (comma-separated)", default=", ".join(site_config.competitors)).split(",")
            if item.strip()
        ],
        geographic_focus=[
            item.strip()
            for item in Prompt.ask(
                "Geographic focus (comma-separated)",
                default=", ".join(site_config.geographic_focus),
            ).split(",")
            if item.strip()
        ],
    )
    save_profile_site_config(get_active_profile() or "default", updated)
    shared.console().print(f"[green]Updated[/green] {settings.resolved_site_config_path}")
