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
