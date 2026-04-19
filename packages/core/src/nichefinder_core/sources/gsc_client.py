from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from nichefinder_core.models.tracking import SearchConsoleRecord
from nichefinder_core.settings import Settings

_GSC_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
_ROW_LIMIT = 25_000  # GSC API max; adequate for a single-site daily sync


class GscClient:
    """Google Search Console API v1 adapter.

    Authenticates via a service account JSON key file whose path is configured
    in settings.gsc_credentials_path. The service account email must be added
    as a Full User on the target GSC property.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.gsc_credentials_path:
            raise ValueError(
                "GSC_CREDENTIALS_PATH is not set. "
                "Add the path to your service account JSON key in .env."
            )
        path = settings.resolve_path(settings.gsc_credentials_path)
        if not path.exists():
            raise FileNotFoundError(f"GSC credentials file not found: {path}")

        from google.oauth2 import service_account

        creds = service_account.Credentials.from_service_account_file(
            str(path), scopes=_GSC_SCOPES
        )
        self._service = build("searchconsole", "v1", credentials=creds, cache_discovery=False)
        self._property_url = settings.gsc_property_url

    def fetch_records(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
        property_url: str | None = None,
    ) -> list[SearchConsoleRecord]:
        """Fetch query+page-level search analytics rows from GSC.

        Defaults to the last 7 days. GSC exposes data with a ~2-day lag so
        end_date defaults to 2 days ago to avoid incomplete rows.
        """
        today = date.today()
        if end_date is None:
            end_date = today - timedelta(days=2)
        if start_date is None:
            start_date = end_date - timedelta(days=6)

        property_id = property_url or self._property_url
        fetched_at = datetime.now(timezone.utc)

        try:
            response = (
                self._service.sites()
                .searchAnalytics()
                .query(
                    siteUrl=property_id,
                    body={
                        "startDate": start_date.isoformat(),
                        "endDate": end_date.isoformat(),
                        "dimensions": ["query", "page", "date"],
                        "rowLimit": _ROW_LIMIT,
                    },
                )
                .execute()
            )
        except HttpError as exc:
            raise RuntimeError(f"GSC API error: {exc.status_code} — {exc.reason}") from exc

        rows = response.get("rows", [])
        records: list[SearchConsoleRecord] = []
        for row in rows:
            keys = row.get("keys", [])
            query, page_url, row_date_str = keys[0], keys[1], keys[2]
            records.append(
                SearchConsoleRecord(
                    query=query,
                    page_url=page_url,
                    impressions=int(row.get("impressions", 0)),
                    clicks=int(row.get("clicks", 0)),
                    ctr=round(float(row.get("ctr", 0.0)), 6),
                    position=round(float(row.get("position", 0.0)), 2),
                    snapshot_date=date.fromisoformat(row_date_str),
                    property_id=property_id,
                    fetched_at=fetched_at,
                )
            )
        return records
