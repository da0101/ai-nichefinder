from collections.abc import Mapping

from sqlalchemy import inspect, text


def apply_additive_sqlite_migrations(engine) -> None:
    if engine.dialect.name != "sqlite":
        return
    inspector = inspect(engine)
    with engine.begin() as connection:
        _ensure_columns(
            connection,
            inspector,
            "keyword",
            {
                "lifecycle_status": "VARCHAR DEFAULT 'discovered'",
                "locale": "VARCHAR DEFAULT 'en'",
                "market": "VARCHAR DEFAULT 'North America'",
                "metrics_fresh_at": "DATETIME",
                "serp_fresh_at": "DATETIME",
                "trend_fresh_at": "DATETIME",
                "score_fresh_at": "DATETIME",
                "metrics_source": "VARCHAR",
                "trend_source": "VARCHAR",
                "score_source": "VARCHAR",
                "score_formula_version": "VARCHAR",
            },
        )
        _ensure_columns(
            connection,
            inspector,
            "contentbriefrecord",
            {
                "schema_version": "VARCHAR DEFAULT 'v1'",
                "score_record_id": "VARCHAR",
                "run_id": "VARCHAR",
                "agent_version": "VARCHAR",
                "model_id": "VARCHAR",
            },
        )
        _ensure_columns(
            connection,
            inspector,
            "serpresult",
            {
                "schema_version": "VARCHAR DEFAULT 'v1'",
                "provider": "VARCHAR DEFAULT 'serpapi'",
                "locale": "VARCHAR",
                "market": "VARCHAR",
                "run_id": "VARCHAR",
                "agent_version": "VARCHAR",
                "model_id": "VARCHAR",
            },
        )
        _backfill_keyword_defaults(connection)


def _ensure_columns(connection, inspector, table_name: str, columns: Mapping[str, str]) -> None:
    existing_tables = set(inspector.get_table_names())
    if table_name not in existing_tables:
        return
    existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
    for name, ddl in columns.items():
        if name in existing_columns:
            continue
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {name} {ddl}"))


def _backfill_keyword_defaults(connection) -> None:
    connection.execute(
        text(
            """
            UPDATE keyword
            SET lifecycle_status = COALESCE(lifecycle_status, 'discovered'),
                locale = COALESCE(locale, 'en'),
                market = COALESCE(market, 'North America'),
                metrics_source = COALESCE(metrics_source, source)
            """
        )
    )
