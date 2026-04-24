from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree

from nichefinder_core.agents.ads_agent import AdsAgent
from nichefinder_core.agents.competitor_agent import CompetitorAgent
from nichefinder_core.agents.content_agent import ContentAgent
from nichefinder_core.agents.keyword_agent import KeywordAgent
from nichefinder_core.agents.serp_agent import SerpAgent
from nichefinder_core.agents.synthesis_agent import SynthesisAgent
from nichefinder_core.agents.trend_agent import TrendAgent
from nichefinder_core.gemini import GeminiClient
from nichefinder_core.models import SiteConfig, load_site_config, save_site_config
from nichefinder_core.sources.bing import BingClient
from nichefinder_core.sources.ddgs import DDGSClient
from nichefinder_core.sources.scraper import ContentScraper
from nichefinder_core.sources.serpapi import SerpAPIClient
from nichefinder_core.sources.tavily import TavilyClient
from nichefinder_core.sources.trends import TrendsClient
from nichefinder_core.sources.yahoo import YahooClient
from nichefinder_core.settings import Settings, get_settings
from nichefinder_core.utils.robots import RobotsChecker
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


@dataclass
class ServiceContainer:
    settings: Settings
    profile_slug: str | None
    gemini: GeminiClient
    serpapi: SerpAPIClient
    tavily: TavilyClient
    ddgs: DDGSClient
    bing: BingClient
    yahoo: YahooClient
    trends: TrendsClient
    scraper: ContentScraper
    keyword_agent: KeywordAgent
    serp_agent: SerpAgent
    trend_agent: TrendAgent
    ads_agent: AdsAgent
    competitor_agent: CompetitorAgent
    synthesis_agent: SynthesisAgent
    content_agent: ContentAgent


def ensure_site_config(settings: Settings) -> SiteConfig:
    slug = current_profile_slug(settings) or "default"
    profile = get_profile_record(slug)
    if profile is not None:
        config = SiteConfig.model_validate_json(profile.site_config_json)
        _sync_site_config_file(slug, config)
        return config

    path = _site_config_path(slug)
    if path.exists():
        config = load_site_config(path)
    else:
        config = SiteConfig()
    save_profile_site_config(slug, config)
    return config


def build_services(settings: Settings, repository: SeoRepository) -> ServiceContainer:
    profile_slug = current_profile_slug(settings)
    gemini = GeminiClient(settings)
    serpapi = SerpAPIClient(settings, repository)
    tavily = TavilyClient(settings, repository)
    ddgs = DDGSClient(settings, repository)
    bing = BingClient(settings, repository)
    yahoo = YahooClient(settings, repository)
    trends = TrendsClient()
    scraper = ContentScraper(
        RobotsChecker(allow_on_error=settings.robots_fetch_fail_open),
        settings,
    )
    return ServiceContainer(
        settings=settings,
        profile_slug=profile_slug,
        gemini=gemini,
        serpapi=serpapi,
        tavily=tavily,
        ddgs=ddgs,
        bing=bing,
        yahoo=yahoo,
        trends=trends,
        scraper=scraper,
        keyword_agent=KeywordAgent(
            settings=settings,
            gemini_client=gemini,
            serpapi_client=serpapi,
            repository=repository,
        ),
        serp_agent=SerpAgent(gemini_client=gemini, serpapi_client=serpapi, repository=repository),
        trend_agent=TrendAgent(trends_client=trends, repository=repository),
        ads_agent=AdsAgent(gemini_client=gemini, repository=repository),
        competitor_agent=CompetitorAgent(
            gemini_client=gemini,
            scraper=scraper,
            repository=repository,
        ),
        synthesis_agent=SynthesisAgent(settings=settings, gemini_client=gemini, repository=repository),
        content_agent=ContentAgent(settings=settings, gemini_client=gemini, repository=repository),
    )


def current_profile_slug(settings: Settings) -> str | None:
    normalized = _normalize_profile_slug(settings.profile_name)
    if normalized in (None, "default"):
        return None
    return normalized


def get_active_profile(settings: Settings | None = None) -> str | None:
    resolved = settings or get_settings()
    if resolved.profile_name:
        return _normalize_profile_slug(resolved.profile_name)

    _bootstrap_profile_registry()
    with get_session(get_settings()) as session:
        state = SeoRepository(session).get_app_state()
        return _normalize_profile_slug(state.active_profile_slug)


def set_active_profile(profile_slug: str | None, settings: Settings | None = None) -> str | None:
    _bootstrap_profile_registry()
    resolved = settings or get_settings()
    normalized = _normalize_profile_slug(profile_slug)
    if normalized == "default":
        normalized = None

    with get_session(get_settings()) as session:
        repository = SeoRepository(session)
        if normalized and repository.get_profile(normalized) is None:
            raise SystemExit(f"Profile not found: {normalized}")
        repository.set_active_profile(normalized)

    active_path = resolved.resolved_active_profile_path
    if normalized is None:
        if active_path.exists():
            active_path.unlink()
        return None

    active_path.parent.mkdir(parents=True, exist_ok=True)
    active_path.write_text(normalized, encoding="utf-8")
    return normalized


def list_profiles(settings: Settings | None = None) -> list[str]:
    del settings
    return [record.slug for record in list_profile_records(include_default=False)]


def list_profile_records(*, include_default: bool = True) -> list:
    _bootstrap_profile_registry()
    with get_session(get_settings()) as session:
        records = SeoRepository(session).list_profiles()
    if include_default:
        return records
    return [record for record in records if record.slug != "default"]


def get_profile_record(profile_slug: str | None):
    normalized = _normalize_profile_slug(profile_slug) or "default"
    _bootstrap_profile_registry()
    with get_session(get_settings()) as session:
        return SeoRepository(session).get_profile(normalized)


def profile_root(profile_slug: str, settings: Settings | None = None) -> Path:
    resolved = settings or get_settings()
    normalized = _normalize_profile_slug(profile_slug)
    if not normalized:
        raise SystemExit("Profile slug cannot be empty.")
    return resolved.resolved_profiles_dir / normalized


def ensure_profile(profile_slug: str, settings: Settings | None = None) -> Path:
    root = profile_root(profile_slug, settings)
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_profile(
    profile_slug: str,
    *,
    site_config: SiteConfig | None = None,
    use: bool = False,
) -> tuple[str, Path]:
    normalized = _normalize_profile_slug(profile_slug)
    if not normalized or normalized == "default":
        raise SystemExit("Profile slug cannot be empty or 'default'.")
    if get_profile_record(normalized) is not None:
        raise SystemExit(f"Profile already exists: {normalized}")

    config = site_config or SiteConfig()
    root = ensure_profile(normalized)
    save_profile_site_config(normalized, config, is_default=False)
    create_db_and_tables(resolve_runtime_settings(normalized))
    if use:
        set_active_profile(normalized)
    return normalized, root


def save_profile_site_config(
    profile_slug: str | None,
    site_config: SiteConfig,
    *,
    is_default: bool | None = None,
) -> SiteConfig:
    normalized = _normalize_profile_slug(profile_slug) or "default"
    _bootstrap_profile_registry()
    with get_session(get_settings()) as session:
        SeoRepository(session).upsert_profile(
            slug=normalized,
            site_name=site_config.site_name,
            site_url=site_config.site_url,
            site_description=site_config.site_description,
            site_config_json=site_config.model_dump_json(),
            is_default=(normalized == "default") if is_default is None else is_default,
        )
    _sync_site_config_file(normalized, site_config)
    return site_config


def delete_profile(profile_slug: str) -> None:
    normalized = _normalize_profile_slug(profile_slug)
    if not normalized or normalized == "default":
        raise SystemExit("The default profile cannot be deleted.")

    _bootstrap_profile_registry()
    with get_session(get_settings()) as session:
        repository = SeoRepository(session)
        if repository.get_profile(normalized) is None:
            raise SystemExit(f"Profile not found: {normalized}")
        if repository.get_app_state().active_profile_slug == normalized:
            repository.set_active_profile(None)
        repository.delete_profile(normalized)

    root = profile_root(normalized)
    config_path = root / "site_config.json"
    if config_path.exists():
        config_path.unlink()
    if root.exists():
        rmtree(root, ignore_errors=True)


def resolve_runtime_settings(profile: str | None = None) -> Settings:
    base_settings = get_settings()
    profile_slug = _normalize_profile_slug(profile) if profile is not None else get_active_profile(base_settings)
    if profile_slug in (None, "default"):
        return base_settings

    root = ensure_profile(profile_slug, base_settings)
    return base_settings.model_copy(
        update={
            "profile_name": profile_slug,
            "database_url": f"sqlite:///{root / 'seo.db'}",
            "site_config_path": root / "site_config.json",
            "cache_dir": root / "cache",
            "outputs_dir": root / "outputs",
            "articles_dir": root / "outputs" / "articles",
            "reports_dir": root / "outputs" / "reports",
            "audits_dir": root / "outputs" / "audits",
        }
    )


def get_runtime(profile: str | None = None):
    settings = resolve_runtime_settings(profile)
    create_db_and_tables(settings)
    site_config = ensure_site_config(settings)
    return settings, site_config, get_session(settings)


def _bootstrap_profile_registry() -> None:
    root_settings = get_settings()
    create_db_and_tables(root_settings)
    with get_session(root_settings) as session:
        repository = SeoRepository(session)

        if repository.get_profile("default") is None:
            default_config = _load_legacy_site_config("default")
            repository.upsert_profile(
                slug="default",
                site_name=default_config.site_name,
                site_url=default_config.site_url,
                site_description=default_config.site_description,
                site_config_json=default_config.model_dump_json(),
                is_default=True,
            )

        profiles_dir = root_settings.resolved_profiles_dir
        if profiles_dir.exists():
            for path in profiles_dir.iterdir():
                if not path.is_dir():
                    continue
                if not (path / "site_config.json").exists():
                    continue
                slug = _normalize_profile_slug(path.name)
                if not slug or repository.get_profile(slug) is not None:
                    continue
                config = _load_legacy_site_config(slug)
                repository.upsert_profile(
                    slug=slug,
                    site_name=config.site_name,
                    site_url=config.site_url,
                    site_description=config.site_description,
                    site_config_json=config.model_dump_json(),
                    is_default=False,
                )

        state = repository.get_app_state()
        if state.active_profile_slug and repository.get_profile(state.active_profile_slug) is not None:
            return

        active_path = root_settings.resolved_active_profile_path
        if not active_path.exists():
            return
        legacy_active = _normalize_profile_slug(active_path.read_text(encoding="utf-8").strip())
        if legacy_active in (None, "default"):
            repository.set_active_profile(None)
        elif repository.get_profile(legacy_active) is not None:
            repository.set_active_profile(legacy_active)


def _load_legacy_site_config(profile_slug: str) -> SiteConfig:
    path = _site_config_path(profile_slug)
    if path.exists():
        return load_site_config(path)
    config = SiteConfig()
    save_site_config(path, config)
    return config


def _site_config_path(profile_slug: str) -> Path:
    settings = get_settings()
    if profile_slug == "default":
        return settings.resolved_site_config_path
    return profile_root(profile_slug, settings) / "site_config.json"


def _sync_site_config_file(profile_slug: str, site_config: SiteConfig) -> None:
    save_site_config(_site_config_path(profile_slug), site_config)


def _normalize_profile_slug(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())
    return normalized or None
