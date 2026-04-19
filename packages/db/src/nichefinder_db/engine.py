from collections.abc import Iterator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.models import (
    ApiUsageRecord,
    Article,
    ArticleVersion,
    CompetitorPage,
    ContentBriefRecord,
    Keyword,
    KeywordCluster,
    KeywordClusterMembership,
    PerformanceRecord,
    RankingSnapshot,
    SerpResult,
)
from nichefinder_core.settings import Settings, get_settings

_REGISTERED_MODELS = (
    ApiUsageRecord,
    Article,
    ArticleVersion,
    CompetitorPage,
    ContentBriefRecord,
    Keyword,
    KeywordCluster,
    KeywordClusterMembership,
    PerformanceRecord,
    RankingSnapshot,
    SerpResult,
)


def get_engine(settings: Settings | None = None):
    resolved_settings = settings or get_settings()
    connect_args = {"check_same_thread": False} if resolved_settings.database_url.startswith("sqlite") else {}
    return create_engine(resolved_settings.database_url, echo=False, connect_args=connect_args)


def create_db_and_tables(settings: Settings | None = None) -> None:
    SQLModel.metadata.create_all(get_engine(settings))


@contextmanager
def get_session(settings: Settings | None = None) -> Iterator[Session]:
    session = Session(get_engine(settings))
    try:
        yield session
    finally:
        session.close()
