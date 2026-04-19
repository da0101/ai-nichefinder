from datetime import date, datetime, timezone
from uuid import uuid4

from sqlmodel import Field, SQLModel


class RankingSnapshot(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    article_id: str = Field(foreign_key="article.id")
    keyword_id: str = Field(foreign_key="keyword.id")
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    position: int | None = None
    page: int | None = None


# Legacy — superseded by SearchConsoleRecord for GSC-sourced data.
class PerformanceRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    article_id: str = Field(foreign_key="article.id")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    average_position: float | None = None


class SearchConsoleRecord(SQLModel, table=True):
    """Query+page-level GSC ingestion record. One row per (query, page, date)."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    keyword_id: str | None = Field(default=None, foreign_key="keyword.id", index=True)
    query: str = Field(index=True)
    page_url: str
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    position: float | None = None
    snapshot_date: date
    property_id: str
    data_source: str = Field(default="gsc")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AnalyticsRecord(SQLModel, table=True):
    """Page-level GA4 ingestion record. One row per (page_url, date)."""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    page_url: str = Field(index=True)
    sessions: int = 0
    bounce_rate: float | None = None
    avg_session_duration_sec: float | None = None
    record_date: date
    property_id: str
    data_source: str = Field(default="ga4")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApiUsageRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    provider: str = Field(index=True)
    usage_month: date = Field(index=True)
    call_count: int = 0
    spend_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
