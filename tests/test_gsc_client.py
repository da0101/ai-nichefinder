"""Tests for GscClient and upsert_search_console_record."""
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.settings import Settings
from nichefinder_db.crud import SeoRepository


def _make_settings(credentials_path: str | None = "/fake/creds.json") -> Settings:
    s = Settings()
    object.__setattr__(s, "gsc_credentials_path", Path(credentials_path) if credentials_path else None)
    object.__setattr__(s, "gsc_property_url", "sc-domain:danilulmashev.com")
    return s


def _repo() -> SeoRepository:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return SeoRepository(Session(engine))


def _fake_gsc_row(query: str, page: str, row_date: str, impressions: int = 100, clicks: int = 5) -> dict:
    return {
        "keys": [query, page, row_date],
        "impressions": impressions,
        "clicks": clicks,
        "ctr": clicks / impressions,
        "position": 8.5,
    }


@patch("nichefinder_core.sources.gsc_client.build")
@patch("google.oauth2.service_account.Credentials.from_service_account_file")
@patch("pathlib.Path.exists", return_value=True)
def test_fetch_maps_api_rows_to_records(mock_exists, mock_creds, mock_build):
    """API rows with (query, page, date) keys map to SearchConsoleRecord fields."""
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.sites.return_value.searchAnalytics.return_value.query.return_value.execute.return_value = {
        "rows": [
            _fake_gsc_row("seo tools", "https://danilulmashev.com/seo-tools", "2026-04-17", 200, 10),
            _fake_gsc_row("web design", "https://danilulmashev.com/web-design", "2026-04-17", 50, 2),
        ]
    }

    from nichefinder_core.sources.gsc_client import GscClient

    client = GscClient(_make_settings())
    records = client.fetch_records(
        start_date=date(2026, 4, 17),
        end_date=date(2026, 4, 17),
    )

    assert len(records) == 2
    r = records[0]
    assert r.query == "seo tools"
    assert r.page_url == "https://danilulmashev.com/seo-tools"
    assert r.impressions == 200
    assert r.clicks == 10
    assert r.snapshot_date == date(2026, 4, 17)
    assert r.property_id == "sc-domain:danilulmashev.com"
    assert r.data_source == "gsc"


@patch("nichefinder_core.sources.gsc_client.build")
@patch("google.oauth2.service_account.Credentials.from_service_account_file")
@patch("pathlib.Path.exists", return_value=True)
def test_empty_api_response_returns_empty_list(mock_exists, mock_creds, mock_build):
    """An API response with no rows returns an empty list, no crash."""
    mock_service = MagicMock()
    mock_build.return_value = mock_service
    mock_service.sites.return_value.searchAnalytics.return_value.query.return_value.execute.return_value = {}

    from nichefinder_core.sources.gsc_client import GscClient

    client = GscClient(_make_settings())
    records = client.fetch_records(start_date=date(2026, 4, 17), end_date=date(2026, 4, 17))
    assert records == []


def test_no_credentials_path_raises():
    """GscClient raises ValueError when GSC_CREDENTIALS_PATH is not set."""
    from nichefinder_core.sources.gsc_client import GscClient

    with pytest.raises(ValueError, match="GSC_CREDENTIALS_PATH"):
        GscClient(_make_settings(credentials_path=None))


def test_upsert_inserts_new_record():
    """upsert_search_console_record inserts a record when none exists."""
    from nichefinder_core.models.tracking import SearchConsoleRecord

    repo = _repo()
    record = SearchConsoleRecord(
        query="seo tools",
        page_url="https://danilulmashev.com/seo-tools",
        impressions=100,
        clicks=5,
        ctr=0.05,
        position=8.5,
        snapshot_date=date(2026, 4, 17),
        property_id="sc-domain:danilulmashev.com",
    )
    saved = repo.upsert_search_console_record(record)
    assert saved.id is not None
    assert saved.impressions == 100


def test_upsert_updates_existing_record():
    """Re-syncing the same (query+page+date+property) updates metrics, not duplicates."""
    from nichefinder_core.models.tracking import SearchConsoleRecord

    repo = _repo()
    base = SearchConsoleRecord(
        query="seo tools",
        page_url="https://danilulmashev.com/seo-tools",
        impressions=100,
        clicks=5,
        ctr=0.05,
        position=8.5,
        snapshot_date=date(2026, 4, 17),
        property_id="sc-domain:danilulmashev.com",
    )
    first = repo.upsert_search_console_record(base)

    refreshed = SearchConsoleRecord(
        query="seo tools",
        page_url="https://danilulmashev.com/seo-tools",
        impressions=180,
        clicks=12,
        ctr=0.067,
        position=6.2,
        snapshot_date=date(2026, 4, 17),
        property_id="sc-domain:danilulmashev.com",
    )
    second = repo.upsert_search_console_record(refreshed)

    assert second.id == first.id
    assert second.impressions == 180
    assert second.clicks == 12
    assert second.position == 6.2

    all_records = repo.list_search_console_records()
    assert len(all_records) == 1
