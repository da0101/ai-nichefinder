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

    google_gemini_api_key: str | None = Field(default=None, alias="GOOGLE_GEMINI_API_KEY")
    serpapi_key: str | None = Field(default=None, alias="SERPAPI_KEY")

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
    scrape_delay_min_seconds: float = Field(default=3.0, alias="SCRAPE_DELAY_MIN_SECONDS")
    scrape_delay_max_seconds: float = Field(default=7.0, alias="SCRAPE_DELAY_MAX_SECONDS")
    max_concurrent_scrapers: int = Field(default=3, alias="MAX_CONCURRENT_SCRAPERS")
    robots_fetch_fail_open: bool = Field(default=False, alias="ROBOTS_FETCH_FAIL_OPEN")

    site_config_path: Path = Field(default=Path("data/site_config.json"), alias="SITE_CONFIG_PATH")
    cache_dir: Path = Field(default=Path("data/cache"), alias="CACHE_DIR")
    content_templates_dir: Path = Field(
        default=Path("data/content_templates"),
        alias="CONTENT_TEMPLATES_DIR",
    )
    outputs_dir: Path = Field(default=Path("outputs"), alias="OUTPUTS_DIR")
    articles_dir: Path = Field(default=Path("outputs/articles"), alias="ARTICLES_DIR")
    reports_dir: Path = Field(default=Path("outputs/reports"), alias="REPORTS_DIR")
    audits_dir: Path = Field(default=Path("outputs/audits"), alias="AUDITS_DIR")

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

    def resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return REPOSITORY_ROOT / path

    @property
    def resolved_site_config_path(self) -> Path:
        return self.resolve_path(self.site_config_path)

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
