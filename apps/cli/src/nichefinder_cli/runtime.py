from dataclasses import dataclass

from nichefinder_core.agents.ads_agent import AdsAgent
from nichefinder_core.agents.competitor_agent import CompetitorAgent
from nichefinder_core.agents.content_agent import ContentAgent
from nichefinder_core.agents.keyword_agent import KeywordAgent
from nichefinder_core.agents.serp_agent import SerpAgent
from nichefinder_core.agents.synthesis_agent import SynthesisAgent
from nichefinder_core.agents.trend_agent import TrendAgent
from nichefinder_core.gemini import GeminiClient
from nichefinder_core.models import SiteConfig, load_site_config, save_site_config
from nichefinder_core.settings import Settings, get_settings
from nichefinder_core.sources.scraper import ContentScraper
from nichefinder_core.sources.serpapi import SerpAPIClient
from nichefinder_core.sources.trends import TrendsClient
from nichefinder_core.utils.robots import RobotsChecker
from nichefinder_db import SeoRepository, get_session


@dataclass
class ServiceContainer:
    gemini: GeminiClient
    serpapi: SerpAPIClient
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
    path = settings.resolved_site_config_path
    if not path.exists():
        default_config = SiteConfig()
        save_site_config(path, default_config)
        return default_config
    return load_site_config(path)


def build_services(settings: Settings, repository: SeoRepository) -> ServiceContainer:
    gemini = GeminiClient(settings)
    serpapi = SerpAPIClient(settings, repository)
    trends = TrendsClient()
    scraper = ContentScraper(
        RobotsChecker(allow_on_error=settings.robots_fetch_fail_open),
        settings,
    )
    return ServiceContainer(
        gemini=gemini,
        serpapi=serpapi,
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


def get_runtime():
    settings = get_settings()
    site_config = ensure_site_config(settings)
    return settings, site_config, get_session(settings)
