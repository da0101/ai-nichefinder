from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProfileRecord(SQLModel, table=True):
    slug: str = Field(primary_key=True, index=True)
    site_name: str = Field(index=True)
    site_url: str = ""
    site_description: str = ""
    site_config_json: str
    is_default: bool = False
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AppStateRecord(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    active_profile_slug: str | None = None
    updated_at: datetime = Field(default_factory=_utcnow)
