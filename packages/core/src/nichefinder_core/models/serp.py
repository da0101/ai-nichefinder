from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class SerpFeatures(BaseModel):
    has_featured_snippet: bool = False
    has_people_also_ask: bool = False
    has_local_pack: bool = False
    has_image_pack: bool = False
    has_video_results: bool = False
    has_shopping_results: bool = False
    ad_count_top: int = 0
    organic_result_count: int = 0


class SerpPage(BaseModel):
    position: int
    title: str
    url: str
    domain: str
    estimated_da: int | None = None
    snippet: str
    content_type: str | None = None


class SerpResult(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    keyword_id: str = Field(foreign_key="keyword.id")
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    features_json: str
    pages_json: str
    competition_analysis: str
    raw_json: str | None = None


class CompetitorPage(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    serp_result_id: str = Field(foreign_key="serpresult.id")
    url: str
    title: str
    word_count: int
    h1: str
    h2_list: str
    h3_list: str
    questions_answered: str
    internal_link_count: int
    external_link_count: int
    has_schema_markup: bool
    estimated_reading_time_min: int
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_summary: str
