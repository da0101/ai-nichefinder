from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class ContentType(str, Enum):
    HOW_TO = "how_to"
    LISTICLE = "listicle"
    COMPARISON = "comparison"
    THOUGHT_LEADERSHIP = "thought_leadership"
    LANDING_PAGE = "landing_page"
    CASE_STUDY = "case_study"


class ContentBrief(BaseModel):
    target_keyword: str
    secondary_keywords: list[str]
    content_type: ContentType
    suggested_title: str
    suggested_h2_structure: list[str]
    questions_to_answer: list[str]
    word_count_target: int
    tone: str
    cta_type: str
    competing_urls: list[str]
    is_rewrite: bool
    existing_article_url: str | None = None
    existing_article_content: str | None = None


class ContentBriefRecord(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    keyword_id: str = Field(foreign_key="keyword.id", index=True)
    brief_json: str
    schema_version: str = Field(default="v1")
    score_record_id: str | None = None
    run_id: str | None = None
    agent_version: str | None = None
    model_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Article(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    keyword_id: str = Field(foreign_key="keyword.id")
    title: str
    slug: str
    content_type: ContentType
    status: str
    word_count: int
    file_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: datetime | None = None
    published_at: datetime | None = None
    published_url: str | None = None
    is_rewrite: bool = False
    original_url: str | None = None


class ArticleVersion(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    article_id: str = Field(foreign_key="article.id", index=True)
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
