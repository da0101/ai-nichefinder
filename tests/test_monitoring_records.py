from datetime import date, timezone
from datetime import datetime as dt

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.models import AnalyticsRecord, Keyword, SearchConsoleRecord, SearchIntent
from nichefinder_db.crud import SeoRepository


def _repo() -> SeoRepository:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return SeoRepository(Session(engine))


def _keyword(repo: SeoRepository) -> Keyword:
    return repo.upsert_keyword(
        Keyword(term="seo tools", seed_keyword="seo tools", source="manual", search_intent=SearchIntent.COMMERCIAL)
    )


def test_save_and_list_search_console_record():
    repo = _repo()
    kw = _keyword(repo)

    record = SearchConsoleRecord(
        keyword_id=kw.id,
        query="seo tools",
        page_url="https://danilulmashev.com/seo-tools",
        impressions=500,
        clicks=40,
        ctr=0.08,
        position=8.3,
        snapshot_date=date(2026, 4, 19),
        property_id="sc-domain:danilulmashev.com",
    )
    saved = repo.save_search_console_record(record)

    assert saved.id is not None
    assert saved.data_source == "gsc"
    assert saved.keyword_id == kw.id

    results = repo.list_search_console_records(keyword_id=kw.id)
    assert len(results) == 1
    assert results[0].impressions == 500
    assert results[0].clicks == 40


def test_list_search_console_records_filters_by_property():
    repo = _repo()

    for prop in ["sc-domain:site-a.com", "sc-domain:site-b.com"]:
        repo.save_search_console_record(
            SearchConsoleRecord(
                query="test query",
                page_url=f"https://{prop}/page",
                snapshot_date=date(2026, 4, 19),
                property_id=prop,
            )
        )

    results = repo.list_search_console_records(property_id="sc-domain:site-a.com")
    assert len(results) == 1
    assert results[0].property_id == "sc-domain:site-a.com"


def test_save_and_list_analytics_record():
    repo = _repo()

    record = AnalyticsRecord(
        page_url="https://danilulmashev.com/seo-tools",
        sessions=120,
        bounce_rate=0.42,
        avg_session_duration_sec=95.5,
        record_date=date(2026, 4, 19),
        property_id="properties/123456789",
    )
    saved = repo.save_analytics_record(record)

    assert saved.id is not None
    assert saved.data_source == "ga4"

    results = repo.list_analytics_records(page_url="https://danilulmashev.com/seo-tools")
    assert len(results) == 1
    assert results[0].sessions == 120
    assert results[0].bounce_rate == 0.42


def test_list_analytics_records_filters_by_property():
    repo = _repo()
    today = date(2026, 4, 19)

    for i in range(3):
        repo.save_analytics_record(
            AnalyticsRecord(
                page_url=f"https://example.com/page-{i}",
                record_date=today,
                property_id="properties/111",
            )
        )
    repo.save_analytics_record(
        AnalyticsRecord(
            page_url="https://example.com/other",
            record_date=today,
            property_id="properties/999",
        )
    )

    results = repo.list_analytics_records(property_id="properties/111")
    assert len(results) == 3


def test_search_console_record_without_keyword_id():
    repo = _repo()

    record = SearchConsoleRecord(
        query="standalone query",
        page_url="https://danilulmashev.com/page",
        snapshot_date=date(2026, 4, 19),
        property_id="sc-domain:danilulmashev.com",
        impressions=10,
        clicks=1,
        ctr=0.1,
    )
    saved = repo.save_search_console_record(record)

    assert saved.keyword_id is None
    results = repo.list_search_console_records()
    assert len(results) == 1
