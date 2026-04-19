import json
import math

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import SYNTHESIS_PROMPT
from nichefinder_core.models import ContentBrief, ContentType, OpportunityScore, compute_opportunity_score


class SynthesisAgentInput(BaseModel):
    keyword_id: str
    site_config: dict
    keyword_data: dict
    serp_data: dict
    trend_data: dict
    ads_data: dict
    competitor_data: dict


class SynthesisAgentOutput(BaseModel):
    opportunity_score: OpportunityScore
    content_brief: ContentBrief | None
    should_create_content: bool
    priority_rank: int


class SynthesisAgent:
    def __init__(self, *, settings, gemini_client, repository):
        self.settings = settings
        self.gemini_client = gemini_client
        self.repository = repository

    def _volume_score(self, volume: int | None, *, source: str) -> float:
        if volume is None and source == "gemini_serpapi":
            return self.settings.unknown_free_source_volume_score
        if not volume or volume <= 0:
            return 0.0
        return min(100.0, round(math.log10(volume + 1) / 4 * 100, 2))

    def _difficulty_score(self, value: int | None, *, source: str) -> float:
        if value is None and source == "gemini_serpapi":
            return self.settings.unknown_free_source_difficulty_score
        return float(max(0, 100 - (value or 100)))

    @staticmethod
    def _trend_score(direction: str | None) -> float:
        return {"rising": 100.0, "stable": 50.0, "declining": 0.0}.get(direction or "", 0.0)

    @staticmethod
    def _intent_score(intent: str | None) -> float:
        return {
            "transactional": 100.0,
            "commercial": 80.0,
            "informational": 60.0,
            "navigational": 20.0,
        }.get(intent or "", 0.0)

    @staticmethod
    def _competition_score(level: str | None) -> float:
        return {"low": 100.0, "medium": 50.0, "high": 10.0}.get(level or "", 0.0)

    async def run(self, payload: SynthesisAgentInput) -> SynthesisAgentOutput:
        keyword = self.repository.get_keyword(payload.keyword_id)
        if keyword is None:
            raise ValueError(f"Keyword not found: {payload.keyword_id}")
        volume_score = self._volume_score(keyword.monthly_volume, source=keyword.source)
        difficulty_score = self._difficulty_score(keyword.difficulty_score, source=keyword.source)
        trend_score = self._trend_score(payload.trend_data["direction"])
        intent_score = self._intent_score(keyword.search_intent.value if keyword.search_intent else None)
        competition_score = self._competition_score(payload.serp_data["competition_level"])
        composite = compute_opportunity_score(
            volume_score=volume_score,
            difficulty_score=difficulty_score,
            trend_score=trend_score,
            intent_score=intent_score,
            competition_score=competition_score,
        )
        if payload.serp_data["rankable"] is False:
            composite = min(composite, 40.0)
        keyword = self.repository.update_keyword(payload.keyword_id, opportunity_score=composite)
        content_brief = None
        should_create_content = composite >= self.settings.min_opportunity_score and payload.serp_data["rankable"]
        llm_context = {
            "why_good_fit": "Keyword not recommended.",
            "content_type": "how_to",
            "suggested_title": keyword.term,
            "suggested_h2_structure": [],
            "questions_to_answer": [],
            "secondary_keywords": [],
            "tone": "accessible",
            "cta_type": "portfolio",
            "action": "skip",
            "existing_article_url": None,
        }
        if should_create_content:
            llm_context = await self.gemini_client.analyze(
                SYNTHESIS_PROMPT.format(
                    keyword=keyword.term,
                    composite_score=composite,
                    volume=keyword.monthly_volume,
                    difficulty=keyword.difficulty_score,
                    trend_direction=payload.trend_data["direction"],
                    intent=keyword.search_intent.value if keyword.search_intent else None,
                    avg_word_count=payload.competitor_data["avg_word_count"],
                    gaps=payload.competitor_data["content_gaps"],
                    paa_questions=payload.serp_data.get("paa_questions", []),
                ),
                json.dumps(payload.model_dump()),
            )
            content_brief = ContentBrief(
                target_keyword=keyword.term,
                secondary_keywords=llm_context.get("secondary_keywords", []),
                content_type=ContentType(llm_context.get("content_type", "how_to")),
                suggested_title=llm_context.get("suggested_title", keyword.term),
                suggested_h2_structure=llm_context.get("suggested_h2_structure", []),
                questions_to_answer=llm_context.get("questions_to_answer", []),
                word_count_target=payload.competitor_data["recommended_word_count"],
                tone=llm_context.get("tone", "accessible"),
                cta_type=llm_context.get("cta_type", "portfolio"),
                competing_urls=payload.keyword_data.get("competing_urls", []),
                is_rewrite=llm_context.get("action") == "rewrite_existing",
                existing_article_url=llm_context.get("existing_article_url"),
                existing_article_content=None,
            )
            self.repository.save_content_brief(payload.keyword_id, content_brief)
        opportunity_score = OpportunityScore(
            keyword_id=keyword.id,
            keyword_term=keyword.term,
            volume_score=volume_score,
            difficulty_score=difficulty_score,
            trend_score=trend_score,
            intent_score=intent_score,
            competition_score=competition_score,
            composite_score=composite,
            why_good_fit=llm_context.get("why_good_fit", ""),
            content_angle=llm_context.get("suggested_title", keyword.term),
            priority="high" if composite >= 80 else "medium" if composite >= 60 else "low",
            action=llm_context.get("action", "skip"),
            existing_article_url=llm_context.get("existing_article_url"),
        )
        return SynthesisAgentOutput(
            opportunity_score=opportunity_score,
            content_brief=content_brief,
            should_create_content=should_create_content,
            priority_rank=0,
        )
