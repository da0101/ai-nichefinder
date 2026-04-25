import json
from datetime import datetime, timezone

from pydantic import BaseModel


class TrendAgentInput(BaseModel):
    keyword_id: str
    keyword_term: str


class TrendAgentOutput(BaseModel):
    keyword_id: str
    direction: str
    trend_data_12m: list[int]
    peak_month: int
    is_seasonal: bool
    related_rising_topics: list[str]
    avg_interest: float


class TrendAgent:
    def __init__(self, *, trends_client, repository):
        self.trends_client = trends_client
        self.repository = repository

    async def run(self, payload: TrendAgentInput) -> TrendAgentOutput:
        interest = await self.trends_client.get_interest_over_time(payload.keyword_term)
        related_topics = await self.trends_client.get_related_topics(payload.keyword_term)
        values = interest["values"]
        avg = round(sum(values) / len(values), 1) if values else 0.0
        output = TrendAgentOutput(
            keyword_id=payload.keyword_id,
            direction=interest["direction"],
            trend_data_12m=values,
            peak_month=max(range(len(values)), key=values.__getitem__) if values else 0,
            is_seasonal=(max(values) - min(values) > 40) if values else False,
            related_rising_topics=related_topics,
            avg_interest=avg,
        )
        self.repository.update_keyword(
            payload.keyword_id,
            trend_direction=output.direction,
            trend_data_12m=json.dumps(output.trend_data_12m),
            trend_fresh_at=datetime.now(timezone.utc),
            trend_source="pytrends",
        )
        return output
