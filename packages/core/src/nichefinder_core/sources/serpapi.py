from datetime import date
from urllib.parse import urlparse

import httpx

from nichefinder_core.models import SerpFeatures, SerpPage
from nichefinder_core.settings import Settings
from nichefinder_core.utils.rate_limiter import serpapi_limiter


class SerpAPIClient:
    BASE_URL = "https://serpapi.com/search"

    def __init__(self, settings: Settings, usage_store=None):
        self.settings = settings
        self.usage_store = usage_store
        self.client = httpx.AsyncClient(timeout=20.0)

    async def _ensure_budget(self) -> None:
        if self.usage_store is None:
            return
        usage = self.usage_store.get_api_usage("serpapi", date.today().replace(day=1))
        used = usage.call_count if usage else 0
        if used >= self.settings.serpapi_calls_per_month:
            raise RuntimeError("SerpAPI monthly limit reached")

    async def search(
        self,
        keyword: str,
        location: str = "United States",
        num_results: int = 10,
    ) -> dict:
        if not self.settings.serpapi_key:
            raise ValueError("SERPAPI_KEY is required")
        await self._ensure_budget()
        await serpapi_limiter.acquire()
        response = await self.client.get(
            self.BASE_URL,
            params={
                "q": keyword,
                "location": location,
                "num": num_results,
                "api_key": self.settings.serpapi_key,
                "output": "json",
            },
        )
        response.raise_for_status()
        if self.usage_store is not None:
            self.usage_store.record_api_usage(provider="serpapi", calls=1)
        return response.json()

    async def get_people_also_ask(self, keyword: str) -> list[str]:
        payload = await self.search(keyword)
        return [item.get("question", "") for item in payload.get("people_also_ask", []) if item.get("question")]

    async def get_related_searches(self, keyword: str) -> list[str]:
        payload = await self.search(keyword)
        return [item.get("query", "") for item in payload.get("related_searches", []) if item.get("query")]

    @staticmethod
    def parse_search_response(payload: dict) -> tuple[SerpFeatures, list[SerpPage], list[str], list[str]]:
        answer_box = payload.get("answer_box", {})
        organic_results = payload.get("organic_results", [])
        inline_videos = payload.get("inline_videos", [])
        related_questions = [item.get("question", "") for item in payload.get("people_also_ask", []) if item.get("question")]
        related_searches = [item.get("query", "") for item in payload.get("related_searches", []) if item.get("query")]
        features = SerpFeatures(
            has_featured_snippet=bool(answer_box),
            has_people_also_ask=bool(payload.get("people_also_ask")),
            has_local_pack=bool(payload.get("local_results")),
            has_image_pack=bool(payload.get("images_results")),
            has_video_results=bool(inline_videos),
            has_shopping_results=bool(payload.get("shopping_results")),
            ad_count_top=len(payload.get("ads", [])),
            organic_result_count=len(organic_results),
        )
        pages = [
            SerpPage(
                position=item.get("position", index + 1),
                title=item.get("title", ""),
                url=item.get("link", ""),
                domain=urlparse(item.get("link", "")).netloc,
                snippet=item.get("snippet", ""),
                content_type=None,
            )
            for index, item in enumerate(organic_results[:10])
        ]
        return features, pages, related_questions, related_searches
