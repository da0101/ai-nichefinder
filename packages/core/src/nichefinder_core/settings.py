from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Application configuration loaded from the local env file."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_env: str = Field(default="development", alias="NICHEFINDER_ENV")
    database_url: str = Field(
        default="sqlite:///data/db/seo.db",
        validation_alias=AliasChoices("NICHEFINDER_DB_URL", "DATABASE_URL"),
    )
    viewer_api_token: str | None = Field(default=None, alias="VIEWER_API_TOKEN")

    google_gemini_api_key: str | None = Field(default=None, alias="GOOGLE_GEMINI_API_KEY")
    serpapi_key: str | None = Field(default=None, alias="SERPAPI_KEY")
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    ddgs_enabled: bool = Field(default=True, alias="DDGS_ENABLED")
    bing_enabled: bool = Field(default=True, alias="BING_ENABLED")
    yahoo_enabled: bool = Field(default=True, alias="YAHOO_ENABLED")

    gemini_flash_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_FLASH_MODEL")
    gemini_pro_model: str = Field(default="gemini-2.5-pro", alias="GEMINI_PRO_MODEL")

    min_opportunity_score: float = Field(default=60.0, alias="MIN_OPPORTUNITY_SCORE")
    max_keyword_difficulty: int = Field(default=50, alias="MAX_KEYWORD_DIFFICULTY")
    min_monthly_volume: int = Field(default=100, alias="MIN_MONTHLY_VOLUME")
    unknown_free_source_volume_score: float = Field(
        default=60.0,
        alias="UNKNOWN_FREE_SOURCE_VOLUME_SCORE",
    )
    unknown_free_source_difficulty_score: float = Field(
        default=60.0,
        alias="UNKNOWN_FREE_SOURCE_DIFFICULTY_SCORE",
    )

    serpapi_calls_per_month: int = Field(default=100, alias="SERPAPI_CALLS_PER_MONTH")
    max_serp_keywords: int = Field(default=8, alias="MAX_SERP_KEYWORDS")
    tavily_credits_per_month: int = Field(default=1000, alias="TAVILY_CREDITS_PER_MONTH")
    max_tavily_keyword_validations: int = Field(default=3, alias="MAX_TAVILY_KEYWORD_VALIDATIONS")
    max_tavily_problem_validations: int = Field(default=2, alias="MAX_TAVILY_PROBLEM_VALIDATIONS")
    ddgs_calls_per_month: int = Field(default=300, alias="DDGS_CALLS_PER_MONTH")
    max_ddgs_keyword_validations: int = Field(default=3, alias="MAX_DDGS_KEYWORD_VALIDATIONS")
    max_ddgs_problem_validations: int = Field(default=2, alias="MAX_DDGS_PROBLEM_VALIDATIONS")
    ddgs_region: str = Field(default="ca-en", alias="DDGS_REGION")
    bing_calls_per_month: int = Field(default=300, alias="BING_CALLS_PER_MONTH")
    max_bing_keyword_validations: int = Field(default=3, alias="MAX_BING_KEYWORD_VALIDATIONS")
    max_bing_problem_validations: int = Field(default=2, alias="MAX_BING_PROBLEM_VALIDATIONS")
    yahoo_calls_per_month: int = Field(default=300, alias="YAHOO_CALLS_PER_MONTH")
    max_yahoo_keyword_validations: int = Field(default=3, alias="MAX_YAHOO_KEYWORD_VALIDATIONS")
    max_yahoo_problem_validations: int = Field(default=2, alias="MAX_YAHOO_PROBLEM_VALIDATIONS")
    max_free_article_keywords: int = Field(default=3, alias="MAX_FREE_ARTICLE_KEYWORDS")
    max_free_article_pages_per_keyword: int = Field(default=2, alias="MAX_FREE_ARTICLE_PAGES_PER_KEYWORD")
    max_free_problem_article_queries: int = Field(default=2, alias="MAX_FREE_PROBLEM_ARTICLE_QUERIES")
    max_free_problem_pages_per_query: int = Field(default=2, alias="MAX_FREE_PROBLEM_PAGES_PER_QUERY")
    free_search_cache_ttl_hours: int = Field(default=72, alias="FREE_SEARCH_CACHE_TTL_HOURS")
    free_article_cache_ttl_hours: int = Field(default=168, alias="FREE_ARTICLE_CACHE_TTL_HOURS")
    free_validation_context_ttl_hours: int = Field(default=24, alias="FREE_VALIDATION_CONTEXT_TTL_HOURS")
    scrape_delay_min_seconds: float = Field(default=3.0, alias="SCRAPE_DELAY_MIN_SECONDS")
    scrape_delay_max_seconds: float = Field(default=7.0, alias="SCRAPE_DELAY_MAX_SECONDS")
    max_concurrent_scrapers: int = Field(default=3, alias="MAX_CONCURRENT_SCRAPERS")
    robots_fetch_fail_open: bool = Field(default=False, alias="ROBOTS_FETCH_FAIL_OPEN")

    site_config_path: Path = Field(default=Path("data/site_config.json"), alias="SITE_CONFIG_PATH")
    profiles_dir: Path = Field(default=Path("data/profiles"), alias="PROFILES_DIR")
    active_profile_path: Path = Field(
        default=Path("data/profiles/.active"),
        alias="ACTIVE_PROFILE_PATH",
    )
    profile_name: str | None = Field(default=None, alias="NICHEFINDER_PROFILE")
    cache_dir: Path = Field(default=Path("data/cache"), alias="CACHE_DIR")
    content_templates_dir: Path = Field(
        default=Path("data/content_templates"),
        alias="CONTENT_TEMPLATES_DIR",
    )
    outputs_dir: Path = Field(default=Path("outputs"), alias="OUTPUTS_DIR")
    articles_dir: Path = Field(default=Path("outputs/articles"), alias="ARTICLES_DIR")
    reports_dir: Path = Field(default=Path("outputs/reports"), alias="REPORTS_DIR")
    audits_dir: Path = Field(default=Path("outputs/audits"), alias="AUDITS_DIR")

    search_location: str = Field(
        default="Montreal, Quebec, Canada",
        alias="SEARCH_LOCATION",
    )

    gsc_credentials_path: Path | None = Field(default=None, alias="GSC_CREDENTIALS_PATH")
    gsc_property_url: str = Field(
        default="sc-domain:danilulmashev.com",
        alias="GSC_PROPERTY_URL",
    )

    site_url: str = Field(default="https://danilulmashev.com", alias="SITE_URL")
    site_name: str = Field(default="Daniil Ulmashev", alias="SITE_NAME")
    primary_language: str = Field(default="en", alias="PRIMARY_LANGUAGE")
    primary_market: str = Field(default="North America", alias="PRIMARY_MARKET")

    @property
    def gsc_ready(self) -> bool:
        return self.gsc_credentials_path is not None and self.gsc_credentials_path.exists()

    @property
    def gemini_ready(self) -> bool:
        return bool(self.google_gemini_api_key)

    @property
    def serpapi_ready(self) -> bool:
        return bool(self.serpapi_key)

    @property
    def tavily_ready(self) -> bool:
        return bool(self.tavily_api_key)

    @property
    def ddgs_ready(self) -> bool:
        return self.ddgs_enabled

    @property
    def bing_ready(self) -> bool:
        return self.bing_enabled

    @property
    def yahoo_ready(self) -> bool:
        return self.yahoo_enabled

    def resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return REPOSITORY_ROOT / path

    @property
    def resolved_site_config_path(self) -> Path:
        return self.resolve_path(self.site_config_path)

    @property
    def resolved_profiles_dir(self) -> Path:
        return self.resolve_path(self.profiles_dir)

    @property
    def resolved_active_profile_path(self) -> Path:
        return self.resolve_path(self.active_profile_path)

    @property
    def resolved_cache_dir(self) -> Path:
        return self.resolve_path(self.cache_dir)

    @property
    def resolved_templates_dir(self) -> Path:
        return self.resolve_path(self.content_templates_dir)

    @property
    def resolved_articles_dir(self) -> Path:
        return self.resolve_path(self.articles_dir)

    @property
    def resolved_reports_dir(self) -> Path:
        return self.resolve_path(self.reports_dir)

    @property
    def resolved_audits_dir(self) -> Path:
        return self.resolve_path(self.audits_dir)

    @staticmethod
    def flag(value: bool) -> str:
        return "yes" if value else "no"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
