from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class SearchIntent(str, Enum):
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class KeywordLifecycleStatus(str, Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    TARGETED = "targeted"


class Keyword(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    term: str = Field(index=True)
    seed_keyword: str
    monthly_volume: int | None = None
    difficulty_score: int | None = None
    cpc_usd: float | None = None
    competition_level: str | None = None
    search_intent: SearchIntent | None = None
    trend_direction: str | None = None
    trend_data_12m: str | None = None
    opportunity_score: float | None = None
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    lifecycle_status: KeywordLifecycleStatus = Field(default=KeywordLifecycleStatus.DISCOVERED)
    locale: str = Field(default="en")
    market: str = Field(default="North America")
    metrics_fresh_at: datetime | None = None
    serp_fresh_at: datetime | None = None
    trend_fresh_at: datetime | None = None
    score_fresh_at: datetime | None = None
    metrics_source: str | None = None
    trend_source: str | None = None
    score_source: str | None = None
    score_formula_version: str | None = None


class KeywordCluster(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    primary_keyword_id: str = Field(foreign_key="keyword.id")
    cluster_name: str
    total_cluster_volume: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KeywordClusterMembership(SQLModel, table=True):
    cluster_id: str = Field(foreign_key="keywordcluster.id", primary_key=True)
    keyword_id: str = Field(foreign_key="keyword.id", primary_key=True)


class OpportunityScore(BaseModel):
    """
    Deterministic opportunity scoring formula.

    composite = (
        volume_score * 0.25
        + difficulty_score * 0.30
        + trend_score * 0.20
        + intent_score * 0.15
        + competition_score * 0.10
    )
    """

    keyword_id: str
    keyword_term: str
    volume_score: float
    difficulty_score: float
    trend_score: float
    intent_score: float
    competition_score: float
    composite_score: float
    why_good_fit: str
    content_angle: str
    priority: str
    action: str
    existing_article_url: str | None = None


class OpportunityScoreRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    keyword_id: str = Field(foreign_key="keyword.id", index=True)
    formula_version: str
    score_source: str
    volume_score: float
    difficulty_score: float
    trend_score: float
    intent_score: float
    competition_score: float
    composite_score: float
    why_good_fit: str
    content_angle: str
    priority: str
    action: str
    existing_article_url: str | None = None
    input_snapshot_json: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def compute_opportunity_score(
    *,
    volume_score: float,
    difficulty_score: float,
    trend_score: float,
    intent_score: float,
    competition_score: float,
) -> float:
    return round(
        (
            volume_score * 0.25
            + difficulty_score * 0.30
            + trend_score * 0.20
            + intent_score * 0.15
            + competition_score * 0.10
        ),
        2,
    )
