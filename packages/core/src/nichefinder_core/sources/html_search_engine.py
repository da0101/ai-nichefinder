from datetime import UTC, date, datetime
from pathlib import Path
import hashlib
import re

import httpx
from bs4 import BeautifulSoup

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.settings import Settings
from nichefinder_core.utils.rate_limiter import search_engine_limiter

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


class HtmlSearchEngineClient:
    provider = "search"
    base_url = ""
    limit_setting = ""
    ready_setting = ""
    debug_on_empty_results = False

    def __init__(self, settings: Settings, usage_store=None):
        self.settings = settings
        self.usage_store = usage_store
        self.client = httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )

    async def _ensure_budget(self, calls_needed: int) -> None:
        if self.usage_store is None:
            return
        usage = self.usage_store.get_api_usage(self.provider, date.today().replace(day=1))
        used = usage.call_count if usage else 0
        limit = int(getattr(self.settings, self.limit_setting))
        if used + calls_needed > limit:
            raise RuntimeError(f"{self.provider} monthly call limit reached")

    async def search(self, query: str, *, max_results: int = 3) -> dict:
        if self.ready_setting and not bool(getattr(self.settings, self.ready_setting, False)):
            raise ValueError(f"{self.provider} validation is disabled")
        cache_key = f"{' '.join(query.lower().split())}::{max_results}"
        cached = load_json_cache(
            self.settings,
            namespace=f"search-results/{self.provider}",
            key=cache_key,
            max_age_hours=self.settings.free_search_cache_ttl_hours,
        )
        if cached is not None:
            return cached
        await self._ensure_budget(1)
        await search_engine_limiter.acquire()
        response = await self.client.get(self.base_url, params=self._params(query, max_results=max_results))
        response.raise_for_status()
        results = self._parse_results(response.text, max_results=max_results)
        if not results and self.debug_on_empty_results:
            self._save_empty_result_debug(query, response.text)
        payload = {"results": results}
        save_json_cache(
            self.settings,
            namespace=f"search-results/{self.provider}",
            key=cache_key,
            payload=payload,
        )
        if self.usage_store is not None:
            self.usage_store.record_api_usage(provider=self.provider, calls=1)
        return payload

    def _params(self, query: str, *, max_results: int) -> dict[str, str | int]:
        raise NotImplementedError

    def _parse_results(self, html: str, *, max_results: int) -> list[dict[str, str]]:
        raise NotImplementedError

    @staticmethod
    def _soup(html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(value.split())

    def _save_empty_result_debug(self, query: str, html: str) -> None:
        debug_dir = self.settings.resolved_cache_dir / "search-debug" / self.provider
        debug_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        slug = self._slugify(query)
        digest = hashlib.sha1(query.encode("utf-8")).hexdigest()[:8]
        target = debug_dir / f"{timestamp}-{slug}-{digest}.html"
        target.write_text(html, encoding="utf-8")

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return normalized[:80] or "query"
