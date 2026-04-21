from datetime import date
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from nichefinder_core.cache_store import load_json_cache, save_json_cache
from nichefinder_core.settings import Settings
from nichefinder_core.sources.html_search_engine import USER_AGENT
from nichefinder_core.utils.rate_limiter import search_engine_limiter


class DDGSClient:
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
        usage = self.usage_store.get_api_usage("ddgs", date.today().replace(day=1))
        used = usage.call_count if usage else 0
        if used + calls_needed > self.settings.ddgs_calls_per_month:
            raise RuntimeError("DDGS monthly call limit reached")

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
        await search_engine_limiter.acquire()
        try:
            response = await self.client.get(
                "https://html.duckduckgo.com/html/",
                params={
                    "q": query,
                    "kl": self.settings.ddgs_region,
                },
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            return {
                "results": [],
                "_error": str(exc),
                "_meta": {
                    "provider": "ddgs",
                    "degraded": True,
                    "degraded_reason": "duckduckgo_unreachable",
                },
            }

        results = self._parse_results(response.text, max_results=max_results)
        if not results:
            return {
                "results": [],
                "_meta": {
                    "provider": "ddgs",
                    "degraded": True,
                    "degraded_reason": "duckduckgo_unparseable",
                },
            }

        payload = {
            "results": results,
            "_meta": {
                "provider": "ddgs",
                "degraded": False,
            },
        }
        save_json_cache(
            self.settings,
            namespace="search-results/ddgs",
            key=cache_key,
            payload=payload,
        )
        if self.usage_store is not None:
            self.usage_store.record_api_usage(provider="ddgs", calls=1)
        return payload

    def _parse_results(self, html: str, *, max_results: int) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "lxml")
        results: list[dict[str, str]] = []
        for node in soup.select("div.result, div.results_links"):
            link = node.select_one("a.result__a")
            if link is None:
                continue
            title = self._clean_text(link.get_text(" ", strip=True))
            url = self._unwrap_url((link.get("href") or "").strip())
            if not title or urlparse(url).scheme not in {"http", "https"}:
                continue
            snippet = ""
            for selector in [".result__snippet", ".result__extras__url", ".result__body"]:
                snippet_node = node.select_one(selector)
                if snippet_node is not None:
                    snippet = self._clean_text(snippet_node.get_text(" ", strip=True))
                if snippet:
                    break
            results.append({"title": title, "url": url, "content": snippet})
            if len(results) >= max_results:
                break
        return results

    @staticmethod
    def _unwrap_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.netloc not in {"duckduckgo.com", "www.duckduckgo.com"}:
            return url
        target = parse_qs(parsed.query).get("uddg")
        if target:
            return unquote(target[0])
        return url

    @staticmethod
    def _clean_text(value: str) -> str:
        return " ".join(value.split())
