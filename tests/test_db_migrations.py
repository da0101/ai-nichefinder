from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from nichefinder_core.settings import Settings
from nichefinder_db import create_db_and_tables


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
