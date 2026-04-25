from datetime import date

import httpx

from nichefinder_core.settings import Settings


class TavilyClient:
    BASE_URL = "https://api.tavily.com/search"

    def __init__(self, settings: Settings, usage_store=None):
        self.settings = settings
        self.usage_store = usage_store
        self.client = httpx.AsyncClient(timeout=20.0)

    async def _ensure_budget(self, credits_needed: int) -> None:
        if self.usage_store is None:
            return
        usage = self.usage_store.get_api_usage("tavily", date.today().replace(day=1))
        used = usage.call_count if usage else 0
        if used + credits_needed > self.settings.tavily_credits_per_month:
            raise RuntimeError("Tavily monthly credit limit reached")

    async def search(
        self,
        query: str,
        *,
        max_results: int = 3,
        search_depth: str = "basic",
        topic: str = "general",
    ) -> dict:
        if not self.settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required")
        credits_needed = 2 if search_depth == "advanced" else 1
        await self._ensure_budget(credits_needed)
        response = await self.client.post(
            self.BASE_URL,
            headers={"Authorization": f"Bearer {self.settings.tavily_api_key}"},
            json={
                "query": query,
                "search_depth": search_depth,
                "topic": topic,
                "max_results": max_results,
                "include_usage": True,
                "include_answer": False,
                "include_raw_content": False,
                "auto_parameters": False,
            },
        )
        response.raise_for_status()
        payload = response.json()
        if self.usage_store is not None:
            credits_used = credits_needed
            usage = payload.get("usage")
            if isinstance(usage, dict):
                credits_used = int(usage.get("api_credits", usage.get("credits_used", credits_needed)))
            self.usage_store.record_api_usage(provider="tavily", calls=credits_used)
        return payload
