from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Application configuration loaded from the local env file."""

    model_config = SettingsConfigDict(
        env_file=REPOSITORY_ROOT / "infra" / "env" / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = Field(default="development", alias="NICHEFINDER_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/nichefinder",
        validation_alias=AliasChoices("NICHEFINDER_DB_URL", "DATABASE_URL"),
    )
    primary_market: str = Field(default="montreal-qc-ca", alias="NICHEFINDER_PRIMARY_MARKET")
    primary_language: str = Field(default="fr", alias="NICHEFINDER_PRIMARY_LANGUAGE")
    secondary_language: str = Field(default="en", alias="NICHEFINDER_SECONDARY_LANGUAGE")
    default_country: str = Field(default="CA", alias="NICHEFINDER_DEFAULT_COUNTRY")
    default_region: str = Field(default="QC", alias="NICHEFINDER_DEFAULT_REGION")
    default_city: str = Field(default="Montreal", alias="NICHEFINDER_DEFAULT_CITY")
    portfolio_url: str | None = Field(default=None, alias="NICHEFINDER_PORTFOLIO_URL")
    cache_dir: Path = Field(default=Path("data/cache"), alias="NICHEFINDER_CACHE_DIR")

    google_ads_developer_token: str | None = Field(default=None, alias="GOOGLE_ADS_DEVELOPER_TOKEN")
    google_ads_customer_id: str | None = Field(default=None, alias="GOOGLE_ADS_CUSTOMER_ID")
    google_ads_login_customer_id: str | None = Field(
        default=None,
        alias="GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    )
    google_oauth_client_id: str | None = Field(default=None, alias="GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: str | None = Field(default=None, alias="GOOGLE_OAUTH_CLIENT_SECRET")
    google_oauth_refresh_token: str | None = Field(default=None, alias="GOOGLE_OAUTH_REFRESH_TOKEN")

    serper_api_key: str | None = Field(default=None, alias="SERPER_API_KEY")
    programmable_search_api_key: str | None = Field(
        default=None,
        alias="PROGRAMMABLE_SEARCH_API_KEY",
    )
    programmable_search_cx: str | None = Field(default=None, alias="PROGRAMMABLE_SEARCH_CX")
    search_console_site_url: str | None = Field(
        default=None,
        alias="GOOGLE_SEARCH_CONSOLE_SITE_URL",
    )
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")

    @property
    def resolved_cache_dir(self) -> Path:
        cache_dir = self.cache_dir
        if not cache_dir.is_absolute():
            cache_dir = REPOSITORY_ROOT / cache_dir
        return cache_dir

    @property
    def google_ads_ready(self) -> bool:
        return all(
            [
                self.google_ads_developer_token,
                self.google_ads_customer_id,
                self.google_oauth_client_id,
                self.google_oauth_client_secret,
                self.google_oauth_refresh_token,
            ]
        )

    @property
    def serper_ready(self) -> bool:
        return bool(self.serper_api_key)

    @property
    def programmable_search_ready(self) -> bool:
        return bool(self.programmable_search_api_key and self.programmable_search_cx)

    @property
    def search_console_ready(self) -> bool:
        return bool(
            self.search_console_site_url
            and self.google_oauth_client_id
            and self.google_oauth_client_secret
            and self.google_oauth_refresh_token
        )

    @property
    def gemini_ready(self) -> bool:
        return bool(self.gemini_api_key)

    @staticmethod
    def flag(value: bool) -> str:
        return "yes" if value else "no"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

