import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from nichefinder_db.base import Base


class KeywordStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ANALYZED = "analyzed"
    WRITTEN = "written"
    PUBLISHED = "published"


class KeywordRecord(Base):
    """
    Stores the keyword entity without inventing exact volume numbers.

    Bucket bounds and supporting signals stay separate so downstream estimates can
    be recalculated transparently.
    """

    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint(
            "normalized_phrase",
            "language",
            "market",
            name="uq_keywords_phrase_language_market",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    normalized_phrase: Mapped[str] = mapped_column(String(512), nullable=False)
    source_seed: Mapped[str | None] = mapped_column(String(512), nullable=True)
    language: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    intent: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[KeywordStatus] = mapped_column(
        Enum(KeywordStatus, name="keyword_status"),
        default=KeywordStatus.DISCOVERED,
        nullable=False,
    )

    demand_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    serp_difficulty: Mapped[float | None] = mapped_column(Float, nullable=True)
    site_rankability: Mapped[float | None] = mapped_column(Float, nullable=True)

    volume_bucket_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume_bucket_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trends_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    autocomplete_depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paa_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

