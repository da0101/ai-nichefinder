from nichefinder_cli.runtime import (
    create_profile,
    delete_profile,
    get_active_profile,
    get_runtime,
    save_profile_site_config,
)
from nichefinder_core.models.site import SiteConfig

from .runtime_context import profile_runtime


def create_profile_action(*, slug: str, from_current: bool = False, use: bool = False, payload: dict | None = None) -> dict:
    if not slug.strip():
        raise ValueError("slug is required")
    if payload is not None:
        source_site_config = SiteConfig.model_validate(payload)
    else:
        source_site_config = get_runtime()[1] if from_current else SiteConfig()
    normalized_slug, _ = create_profile(slug, site_config=source_site_config, use=use)
    target_settings = get_runtime(normalized_slug)[0]
    return {
        "slug": normalized_slug,
        "site_config": source_site_config.model_dump(),
        "site_config_path": str(target_settings.resolved_site_config_path),
        "database_url": target_settings.database_url,
        "active": use,
    }


def load_profile_config(profile_slug: str | None = None) -> dict:
    slug, settings, site_config = profile_runtime(profile_slug)
    return {
        "profile": slug,
        "site_config": site_config.model_dump(),
        "paths": {
            "site_config_path": str(settings.resolved_site_config_path),
            "database_url": settings.database_url,
        },
    }


def save_profile_config_action(*, profile_slug: str | None = None, payload: dict) -> dict:
    slug, _, _ = profile_runtime(profile_slug)
    config = SiteConfig.model_validate(payload)
    save_profile_site_config(slug, config)
    return load_profile_config(slug)


def delete_profile_action(*, profile_slug: str) -> dict:
    slug, _, _ = profile_runtime(profile_slug)
    delete_profile(slug)
    active = get_active_profile() or "default"
    return {"deleted": slug, "active_profile": active}
