from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.models import (
    AnalyticsRecord,
    ApiUsageRecord,
    Article,
    ArticleVersion,
    CompetitorPage,
    ContentBriefRecord,
    Keyword,
    KeywordCluster,
    KeywordClusterMembership,
    OpportunityScoreRecord,
    PerformanceRecord,
    RankingSnapshot,
    SearchConsoleRecord,
    SerpResult,
)
from nichefinder_core.settings import Settings, get_settings
from nichefinder_db.migrations import apply_additive_sqlite_migrations

_REGISTERED_MODELS = (
    AnalyticsRecord,
    ApiUsageRecord,
    Article,
    ArticleVersion,
    CompetitorPage,
    ContentBriefRecord,
    Keyword,
    KeywordCluster,
    KeywordClusterMembership,
    OpportunityScoreRecord,
    PerformanceRecord,
    RankingSnapshot,
    SearchConsoleRecord,
    SerpResult,
)


def get_engine(settings: Settings | None = None):
    resolved_settings = settings or get_settings()
    connect_args = {"check_same_thread": False} if resolved_settings.database_url.startswith("sqlite") else {}
    return create_engine(resolved_settings.database_url, echo=False, connect_args=connect_args)


def create_db_and_tables(settings: Settings | None = None) -> None:
    engine = get_engine(settings)
    SQLModel.metadata.create_all(engine)
    apply_additive_sqlite_migrations(engine)


@contextmanager
def get_session(settings: Settings | None = None) -> Iterator[Session]:
    session = Session(get_engine(settings))
    try:
        yield session
    finally:
        session.close()
