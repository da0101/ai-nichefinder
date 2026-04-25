import asyncio
from datetime import date, timedelta

from nichefinder_cli.runtime import build_services
from nichefinder_cli.workflows import check_rankings
from nichefinder_core.settings import Settings
from nichefinder_core.sources.gsc_client import GscClient
from nichefinder_db import SeoRepository

from nichefinder_cli.viewer_api_models import MonitorSyncResponse, RankCheckResponse, RankCheckRow

from .runtime_context import session_runtime


def run_monitor_sync_action(
    *,
    profile_slug: str | None = None,
    days: int = 7,
    property_url: str | None = None,
    settings_override: Settings | None = None,
) -> MonitorSyncResponse:
    slug, settings, _, session_context = session_runtime(profile_slug, settings_override)
    if not settings.gsc_credentials_path:
        raise ValueError(
            "GSC_CREDENTIALS_PATH is not configured. Add the path to your service account JSON key in .env."
        )
    client = GscClient(settings)
    end_date = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=days - 1)
    records = client.fetch_records(
        start_date=start_date,
        end_date=end_date,
        property_url=property_url,
    )
    inserted = 0
    updated = 0
    with session_context as session:
        repository = SeoRepository(session)
        for record in records:
            existing = repository.find_search_console_record(
                record.query,
                record.page_url,
                record.snapshot_date,
                record.property_id,
            )
            repository.upsert_search_console_record(record)
            if existing is None:
                inserted += 1
            else:
                updated += 1
    return MonitorSyncResponse(
        profile=slug,
        days=days,
        property_url=property_url or settings.gsc_property_url,
        start_date=start_date,
        end_date=end_date,
        total_rows=len(records),
        inserted=inserted,
        updated=updated,
    )


def run_rank_check_action(
    *,
    profile_slug: str | None = None,
    skip_recent: bool = True,
    settings_override: Settings | None = None,
) -> RankCheckResponse:
    slug, settings, _, session_context = session_runtime(profile_slug, settings_override)
    with session_context as session:
        repository = SeoRepository(session)
        services = build_services(settings, repository)
        rows = asyncio.run(check_rankings(services, repository, skip_recent=skip_recent))
    return RankCheckResponse(
        profile=slug,
        skip_recent=skip_recent,
        rows=[
            RankCheckRow(
                article_id=row["article"].id,
                article_title=row["article"].title,
                keyword_id=row["keyword"].id,
                keyword_term=row["keyword"].term,
                last_position=row["last"].position if row["last"] else None,
                current_position=row["snapshot"].position,
                change=(
                    row["last"].position - row["snapshot"].position
                    if row["last"] and row["last"].position and row["snapshot"].position
                    else None
                ),
                checked_at=row["snapshot"].checked_at.isoformat(),
            )
            for row in rows
        ],
    )
