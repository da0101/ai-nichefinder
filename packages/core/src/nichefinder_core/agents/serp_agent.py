import json

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import SERP_ANALYSIS_PROMPT
from nichefinder_core.models import SerpResult


class SerpAgentInput(BaseModel):
    keyword_id: str
    keyword_term: str
    location: str = "United States"


class SerpAgentOutput(BaseModel):
    keyword_id: str
    serp_result_id: str
    pages_analyzed: int
    features_detected: list[str]
    competition_level: str
    rankable: bool


class SerpAgent:
    def __init__(self, *, gemini_client, serpapi_client, repository):
        self.gemini_client = gemini_client
        self.serpapi_client = serpapi_client
        self.repository = repository

    async def run(self, payload: SerpAgentInput) -> SerpAgentOutput:
        raw_serp = await self.serpapi_client.search(payload.keyword_term, payload.location)
        features, pages, paa_questions, related_searches = self.serpapi_client.parse_search_response(raw_serp)
        analysis = await self.gemini_client.analyze(
            SERP_ANALYSIS_PROMPT.format(keyword=payload.keyword_term, serp_json=json.dumps(raw_serp)),
            json.dumps({"pages": [page.model_dump() for page in pages], "paa": paa_questions}),
        )
        serp_result = SerpResult(
            keyword_id=payload.keyword_id,
            features_json=features.model_dump_json(),
            pages_json=json.dumps([page.model_dump() for page in pages]),
            competition_analysis=json.dumps(analysis),
            raw_json=json.dumps(raw_serp),
        )
        saved = self.repository.create_serp_result(serp_result)
        features_detected = [
            name
            for name, enabled in features.model_dump().items()
            if isinstance(enabled, bool) and enabled
        ]
        return SerpAgentOutput(
            keyword_id=payload.keyword_id,
            serp_result_id=saved.id,
            pages_analyzed=len(pages),
            features_detected=features_detected,
            competition_level=analysis.get("competition_level", "medium"),
            rankable=bool(analysis.get("rankable", False)),
        )
