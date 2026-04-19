import json

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import SERP_ANALYSIS_PROMPT
from nichefinder_core.models import SerpResult
from nichefinder_core.utils.serp_signals import estimate_difficulty


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
    difficulty_estimate: int


class SerpAgent:
    def __init__(
        self,
        *,
        gemini_client,
        serpapi_client,
        repository,
        agent_version: str | None = None,
        model_id: str | None = None,
    ):
        self.gemini_client = gemini_client
        self.serpapi_client = serpapi_client
        self.repository = repository
        self.agent_version = agent_version
        self.model_id = model_id

    async def run(self, payload: SerpAgentInput, *, run_id: str | None = None) -> SerpAgentOutput:
        raw_serp = await self.serpapi_client.search(payload.keyword_term, payload.location)
        features, pages, paa_questions, related_searches = self.serpapi_client.parse_search_response(raw_serp)
        analysis = await self.gemini_client.analyze(
            SERP_ANALYSIS_PROMPT.format(keyword=payload.keyword_term, serp_json=json.dumps(raw_serp)),
            json.dumps({"pages": [page.model_dump() for page in pages], "paa": paa_questions}),
        )
        keyword = self.repository.get_keyword(payload.keyword_id)
        serp_result = SerpResult(
            keyword_id=payload.keyword_id,
            schema_version="v2",
            provider="serpapi",
            locale=keyword.locale if keyword else None,
            market=payload.location,
            features_json=features.model_dump_json(),
            pages_json=json.dumps([page.model_dump() for page in pages]),
            competition_analysis=json.dumps(analysis),
            raw_json=json.dumps(raw_serp),
            run_id=run_id,
            agent_version=self.agent_version,
            model_id=self.model_id,
        )
        saved = self.repository.create_serp_result(serp_result)
        difficulty_estimate = estimate_difficulty(features, pages)
        keyword_updates: dict = {"serp_fresh_at": saved.fetched_at}
        if keyword is None or keyword.difficulty_score is None:
            keyword_updates["difficulty_score"] = difficulty_estimate
        self.repository.update_keyword(payload.keyword_id, **keyword_updates)
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
            difficulty_estimate=difficulty_estimate,
        )
