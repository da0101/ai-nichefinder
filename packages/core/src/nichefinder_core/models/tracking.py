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


class PerformanceRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    article_id: str = Field(foreign_key="article.id")
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    average_position: float | None = None


class ApiUsageRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    provider: str = Field(index=True)
    usage_month: date = Field(index=True)
    call_count: int = 0
    spend_usd: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
