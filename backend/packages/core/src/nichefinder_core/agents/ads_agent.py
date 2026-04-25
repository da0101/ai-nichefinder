import json

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import ADS_ANALYSIS_PROMPT


class AdsAgentInput(BaseModel):
    keyword_id: str
    keyword_term: str


class AdsAgentOutput(BaseModel):
    keyword_id: str
    cpc_usd: float | None
    competition_level: str | None
    monthly_ad_volume: int | None
    commercial_intent_score: int
    top_ad_angles: list[str]


class AdsAgent:
    def __init__(self, *, gemini_client, repository):
        self.gemini_client = gemini_client
        self.repository = repository

    async def run(self, payload: AdsAgentInput) -> AdsAgentOutput:
        keyword = self.repository.get_keyword(payload.keyword_id)
        serp_result = self.repository.get_latest_serp_result(payload.keyword_id)
        raw_json = json.loads(serp_result.raw_json or "{}") if serp_result else {}
        ads = raw_json.get("ads", [])
        if keyword is None:
            raise ValueError(f"Keyword not found: {payload.keyword_id}")
        cpc = keyword.cpc_usd
        ad_count = len(ads)
        if cpc is None:
            score = 20 if ad_count else 0
        elif cpc > 5:
            score = 90
        elif cpc >= 2:
            score = 65
        else:
            score = 35 if ad_count else 20
        ad_analysis = {"top_ad_angles": []}
        if ads:
            ad_analysis = await self.gemini_client.analyze(
                ADS_ANALYSIS_PROMPT.format(ads_json=json.dumps(ads)),
                json.dumps(ads),
            )
        return AdsAgentOutput(
            keyword_id=payload.keyword_id,
            cpc_usd=cpc,
            competition_level=keyword.competition_level,
            monthly_ad_volume=ad_count if ad_count else None,
            commercial_intent_score=score,
            top_ad_angles=ad_analysis.get("top_ad_angles", []),
        )
