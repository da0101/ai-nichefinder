from nichefinder_cli.runtime import get_active_profile, get_runtime, get_profile_record, list_profile_records, list_profiles, set_active_profile
from nichefinder_core.noise_memory import approve_training_entries, learning_memory_stats, load_noise_profile, summarize_training_candidates
from nichefinder_db import SeoRepository


def load_profiles() -> dict:
    active = get_active_profile() or "default"
    records = list_profile_records(include_default=True)
    profiles: list[dict] = []
    for record in records:
        slug = record.slug
        settings, site_config, session_context = get_runtime(slug)
        with session_context as session:
            repository = SeoRepository(session)
            stats = learning_memory_stats(settings, site_config=site_config.model_dump())
            profiles.append(
                {
                    "slug": slug,
                    "site_name": site_config.site_name,
                    "site_url": site_config.site_url,
                    "site_description": site_config.site_description,
                    "is_default": slug == "default",
                    "site_config": site_config.model_dump(),
                    "database_url": settings.database_url,
                    "keywords": len(repository.list_keywords()),
                    "articles": len(repository.list_articles()),
                    "runs": stats["runs"],
                    "approved_noise": stats["approved_noise"],
                    "approved_validity": stats["approved_validity"],
                    "approved_legitimacy": stats["approved_legitimacy"],
                }
            )
    return {"active_profile": active, "profiles": profiles}


def switch_active_profile(profile_slug: str | None) -> dict:
    if profile_slug not in (None, "", "default") and get_profile_record(profile_slug) is None:
        raise ValueError(f"profile not found: {profile_slug}")
    set_active_profile(None if profile_slug in (None, "", "default") else profile_slug)
    return load_profiles()


def load_training_review(*, profile_slug: str | None = None, min_runs: int = 2, limit: int = 18) -> dict:
    slug = _resolved_slug(profile_slug)
    settings, site_config, _ = get_runtime(slug)
    approved = load_noise_profile(settings, site_config=site_config.model_dump())
    stats = learning_memory_stats(settings, site_config=site_config.model_dump())
    candidates = summarize_training_candidates(
        settings,
        site_config=site_config.model_dump(),
        min_runs=min_runs,
        limit=limit,
    )
    return {
        "profile": {
            "slug": slug,
            "site_name": site_config.site_name,
            "site_url": site_config.site_url,
            "runs": stats["runs"],
            "approved_noise": stats["approved_noise"],
            "approved_validity": stats["approved_validity"],
            "approved_legitimacy": stats["approved_legitimacy"],
        },
        "approved": {
            "noise": {
                "keyword_phrases": approved.keyword_phrases,
                "secondary_phrases": approved.secondary_phrases,
                "domains": approved.domains,
            },
            "validity": {
                "keyword_phrases": approved.valid_keyword_phrases,
                "secondary_phrases": approved.valid_secondary_phrases,
            },
            "legitimacy": {
                "domains": approved.trusted_domains,
            },
        },
        "candidates": [
            {
                "scope": item.scope,
                "label": item.label,
                "value": item.value,
                "support_runs": item.support_runs,
                "support_count": item.support_count,
                "examples": item.examples,
            }
            for item in candidates
        ],
    }


def approve_training_review(
    *,
    profile_slug: str | None = None,
    noise_keyword_phrases: list[str] | None = None,
    noise_secondary_phrases: list[str] | None = None,
    noise_domains: list[str] | None = None,
    valid_keyword_phrases: list[str] | None = None,
    valid_secondary_phrases: list[str] | None = None,
    trusted_domains: list[str] | None = None,
    min_runs: int = 2,
    limit: int = 18,
) -> dict:
    slug = _resolved_slug(profile_slug)
    settings, site_config, _ = get_runtime(slug)
    approve_training_entries(
        settings,
        site_config=site_config.model_dump(),
        noise_keyword_phrases=noise_keyword_phrases,
        noise_secondary_phrases=noise_secondary_phrases,
        noise_domains=noise_domains,
        valid_keyword_phrases=valid_keyword_phrases,
        valid_secondary_phrases=valid_secondary_phrases,
        trusted_domains=trusted_domains,
    )
    return load_training_review(profile_slug=slug, min_runs=min_runs, limit=limit)


def load_final_review(*, profiles: list[str] | None = None, min_runs: int = 2, limit: int = 9) -> dict:
    selected = profiles or list_profiles()
    if not selected:
        selected = ["default"]

    rows: list[dict] = []
    shared_valid_keywords: set[str] | None = None
    shared_trusted_domains: set[str] | None = None
    per_profile: list[dict] = []
    for slug in selected:
        resolved_slug = _resolved_slug(slug)
        settings, site_config, _ = get_runtime(resolved_slug)
        stats = learning_memory_stats(settings, site_config=site_config.model_dump())
        rows.append(
            {
                "slug": resolved_slug,
                "runs": stats["runs"],
                "approved_noise": stats["approved_noise"],
                "approved_validity": stats["approved_validity"],
                "approved_legitimacy": stats["approved_legitimacy"],
            }
        )
        profile = load_noise_profile(settings, site_config=site_config.model_dump())
        valid_keywords = set(profile.valid_keyword_phrases)
        trusted_domains = set(profile.trusted_domains)
        shared_valid_keywords = valid_keywords if shared_valid_keywords is None else shared_valid_keywords & valid_keywords
        shared_trusted_domains = trusted_domains if shared_trusted_domains is None else shared_trusted_domains & trusted_domains
        per_profile.append(load_training_review(profile_slug=resolved_slug, min_runs=min_runs, limit=limit))
    return {
        "summary": rows,
        "shared_valid_keywords": sorted(shared_valid_keywords or []),
        "shared_trusted_domains": sorted(shared_trusted_domains or []),
        "profiles": per_profile,
    }


def _resolved_slug(profile_slug: str | None) -> str:
    if profile_slug in (None, ""):
        return get_active_profile(resolve_runtime_settings()) or "default"
    if profile_slug == "default":
        return "default"
    return profile_slug
