from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlmodel import Session, SQLModel

from nichefinder_core.models import Keyword, SerpResult
from nichefinder_core.settings import Settings
from nichefinder_db import create_db_and_tables
from nichefinder_db.crud import SeoRepository


def test_create_db_and_tables_adds_v2_keyword_columns_and_score_table(tmp_path: Path):
    db_path = tmp_path / "legacy.db"
    legacy_engine = create_engine(f"sqlite:///{db_path}")
    with legacy_engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE keyword (
                    id VARCHAR PRIMARY KEY,
                    term VARCHAR,
                    seed_keyword VARCHAR,
                    monthly_volume INTEGER,
                    difficulty_score INTEGER,
                    cpc_usd FLOAT,
                    competition_level VARCHAR,
                    search_intent VARCHAR,
                    trend_direction VARCHAR,
                    trend_data_12m VARCHAR,
                    opportunity_score FLOAT,
                    discovered_at DATETIME,
                    source VARCHAR
                )
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO keyword (id, term, seed_keyword, discovered_at, source)
                VALUES ('kw-1', 'legacy keyword', 'legacy keyword', '2026-04-19T00:00:00Z', 'manual')
                """
            )
        )

    create_db_and_tables(Settings(database_url=f"sqlite:///{db_path}"))

    inspector = inspect(create_engine(f"sqlite:///{db_path}"))
    keyword_columns = {column["name"] for column in inspector.get_columns("keyword")}

    assert "lifecycle_status" in keyword_columns
    assert "locale" in keyword_columns
    assert "market" in keyword_columns
    assert "score_formula_version" in keyword_columns
    assert "opportunityscorerecord" in set(inspector.get_table_names())

    table_names = set(inspector.get_table_names())
    assert "searchconsolerecord" in table_names
    assert "analyticsrecord" in table_names

    serp_columns = {column["name"] for column in inspector.get_columns("serpresult")}
    assert "run_id" in serp_columns
    assert "agent_version" in serp_columns
    assert "model_id" in serp_columns

    brief_columns = {column["name"] for column in inspector.get_columns("contentbriefrecord")}
    assert "run_id" in brief_columns
    assert "agent_version" in brief_columns
    assert "model_id" in brief_columns


def test_serp_result_provenance_fields_round_trip():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    repo = SeoRepository(session)

    keyword = repo.upsert_keyword(
        Keyword(term="provenance test", seed_keyword="provenance test", source="manual")
    )
    serp = SerpResult(
        keyword_id=keyword.id,
        features_json="{}",
        pages_json="[]",
        competition_analysis="{}",
        run_id="run-abc123",
        agent_version="serp-agent-v1",
        model_id="gemini-2.5-flash",
    )
    saved = repo.create_serp_result(serp)

    fetched = repo.get_latest_serp_result(keyword.id)
    assert fetched is not None
    assert fetched.run_id == "run-abc123"
    assert fetched.agent_version == "serp-agent-v1"
    assert fetched.model_id == "gemini-2.5-flash"


def test_freshness_fields_written_by_update_keyword():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    repo = SeoRepository(session)

    keyword = repo.upsert_keyword(
        Keyword(term="freshness test", seed_keyword="freshness test", source="manual")
    )
    assert keyword.serp_fresh_at is None
    assert keyword.trend_fresh_at is None

    now = datetime.now(timezone.utc)
    repo.update_keyword(keyword.id, serp_fresh_at=now, trend_fresh_at=now)

    updated = repo.get_keyword(keyword.id)
    assert updated is not None
    assert updated.serp_fresh_at is not None
    assert updated.trend_fresh_at is not None


def test_create_db_and_tables_resolves_default_relative_sqlite_path_from_repo_root():
    settings = Settings()
    repo_relative = Path(".tmp-test-db/relative.db")
    settings.database_url = f"sqlite:///{repo_relative}"
    expected_path = settings.resolve_path(repo_relative)
    try:
        create_db_and_tables(settings)
        assert expected_path.exists()
    finally:
        wal_path = expected_path.with_name(f"{expected_path.name}-wal")
        shm_path = expected_path.with_name(f"{expected_path.name}-shm")
        for path in [wal_path, shm_path, expected_path]:
            if path.exists():
                path.unlink()
        if expected_path.parent.exists():
            expected_path.parent.rmdir()
