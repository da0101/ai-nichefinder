from nichefinder_cli.runtime import (
    ensure_site_config,
    get_active_profile,
    get_runtime,
    resolve_runtime_settings,
)
from nichefinder_core.models.site import SiteConfig
from nichefinder_core.settings import Settings
from nichefinder_db import create_db_and_tables, get_session


def profile_runtime(profile_slug: str | None) -> tuple[str, Settings, SiteConfig]:
    if profile_slug in (None, ""):
        slug = get_active_profile(resolve_runtime_settings()) or "default"
    elif profile_slug == "default":
        slug = "default"
    else:
        slug = profile_slug
    settings, site_config, _ = get_runtime(slug)
    return slug, settings, site_config


def session_runtime(
    profile_slug: str | None,
    settings_override: Settings | None = None,
) -> tuple[str, Settings, SiteConfig, object]:
    if settings_override is None:
        slug, settings, site_config = profile_runtime(profile_slug)
        return slug, settings, site_config, get_runtime(slug)[2]
    expected_slug = settings_override.profile_name or "default"
    if profile_slug in (None, "", expected_slug) or (profile_slug == "default" and expected_slug == "default"):
        create_db_and_tables(settings_override)
        site_config = ensure_site_config(settings_override)
        return expected_slug, settings_override, site_config, get_session(settings_override)
    slug, settings, site_config = profile_runtime(profile_slug)
    return slug, settings, site_config, get_runtime(slug)[2]
