from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
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
    database_url = _resolve_database_url(resolved_settings)
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, echo=False, connect_args=connect_args)
    if database_url.startswith("sqlite"):
        with engine.connect() as conn:
            conn.execute(text("PRAGMA journal_mode=WAL"))
            conn.execute(text("PRAGMA synchronous=NORMAL"))
    return engine


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


def _resolve_database_url(settings: Settings) -> str:
    url = make_url(settings.database_url)
    if url.drivername != "sqlite":
        return settings.database_url
    if url.database in (None, "", ":memory:"):
        return settings.database_url

    db_path = Path(url.database)
    if not db_path.is_absolute():
        db_path = settings.resolve_path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"
