import asyncio
from datetime import date

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.settings import Settings

try:
    from ddgs import DDGS
except ImportError:  # pragma: no cover - exercised in runtime only when dependency is missing
    DDGS = None


class DDGSClient:
    def __init__(self, settings: Settings, usage_store=None):
        self.settings = settings
        self.usage_store = usage_store

    async def _ensure_budget(self, calls_needed: int) -> None:
        if self.usage_store is None:
            return
        usage = self.usage_store.get_api_usage("ddgs", date.today().replace(day=1))
        used = usage.call_count if usage else 0
        if used + calls_needed > self.settings.ddgs_calls_per_month:
            raise RuntimeError("DDGS monthly call limit reached")

    def _search_sync(self, query: str, *, max_results: int, backend: str) -> dict:
        if DDGS is None:
            raise RuntimeError("ddgs package is not installed")

        client = DDGS(timeout=8)
        try:
            results = client.text(
                query,
                region=self.settings.ddgs_region,
                safesearch="moderate",
                max_results=max_results,
                backend=backend,
            )
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()
        return {
            "results": [
                {
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "content": item.get("body", ""),
                }
                for item in results or []
            ]
        }

    async def search(self, query: str, *, max_results: int = 3) -> dict:
        if not self.settings.ddgs_ready:
            raise ValueError("DDGS validation is disabled")
        cache_key = f"{' '.join(query.lower().split())}::{max_results}"
        cached = load_json_cache(
            self.settings,
            namespace="search-results/ddgs",
            key=cache_key,
            max_age_hours=self.settings.free_search_cache_ttl_hours,
        )
        if cached is not None:
            return cached

        await self._ensure_budget(1)
        try:
            payload = await asyncio.to_thread(
                self._search_sync,
                query,
                max_results=max_results,
                backend="duckduckgo",
            )
        except Exception:
            payload = await asyncio.to_thread(
                self._search_sync,
                query,
                max_results=max_results,
                backend="auto",
            )

        save_json_cache(
            self.settings,
            namespace="search-results/ddgs",
            key=cache_key,
            payload=payload,
        )
        if self.usage_store is not None:
            self.usage_store.record_api_usage(provider="ddgs", calls=1)
        return payload
