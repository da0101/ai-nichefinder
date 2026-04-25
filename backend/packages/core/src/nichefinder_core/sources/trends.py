import asyncio
import random

from pytrends.request import TrendReq


class TrendsClient:
    def __init__(self):
        self.pytrends = TrendReq(hl="en-US", tz=360, timeout=(10, 25))

    async def get_interest_over_time(self, keyword: str, timeframe: str = "today 12-m") -> dict:
        await asyncio.sleep(random.uniform(2.0, 3.0))
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_interest, keyword, timeframe)

    def _fetch_interest(self, keyword: str, timeframe: str) -> dict:
        try:
            self.pytrends.build_payload([keyword], timeframe=timeframe)
            df = self.pytrends.interest_over_time()
            values = [] if df.empty else [int(value) for value in df[keyword].tolist()[-12:]]
        except Exception:
            # pytrends is unofficial and gets rate-limited (429) frequently.
            # Degrade gracefully — scoring falls back to neutral trend.
            values = []
        if not values:
            values = [0] * 12
        midpoint = max(len(values) // 2, 1)
        first_avg = sum(values[:midpoint]) / midpoint
        second_avg = sum(values[midpoint:]) / max(len(values[midpoint:]), 1)
        if second_avg > first_avg * 1.2:
            direction = "rising"
        elif second_avg < first_avg * 0.8:
            direction = "declining"
        else:
            direction = "stable"
        return {"values": values, "direction": direction}

    async def get_related_topics(self, keyword: str) -> list[str]:
        await asyncio.sleep(random.uniform(2.0, 3.0))
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._fetch_related_topics, keyword)

    def _fetch_related_topics(self, keyword: str) -> list[str]:
        self.pytrends.build_payload([keyword], timeframe="today 12-m")
        try:
            related_topics = self.pytrends.related_topics()
        except (IndexError, KeyError, TypeError):
            return []
        rising = related_topics.get(keyword, {}).get("rising")
        if rising is None or rising.empty:
            return []
        return [str(topic) for topic in rising["topic_title"].dropna().tolist()[:10]]
