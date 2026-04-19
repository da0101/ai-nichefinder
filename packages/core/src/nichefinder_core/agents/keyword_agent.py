import json
from typing import Any

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import KEYWORD_EXPANSION_PROMPT, KEYWORD_INTENT_PROMPT
from nichefinder_core.models import Keyword, KeywordLifecycleStatus, SearchIntent
from nichefinder_core.settings import Settings


class KeywordAgentInput(BaseModel):
    seed_keyword: str
    site_config: dict
    max_keywords: int = 50


class KeywordAgentOutput(BaseModel):
    seed_keyword: str
    keywords_found: int
    keywords_saved: int
    keyword_ids: list[str]


class KeywordAgent:
    def __init__(self, *, settings: Settings, gemini_client, serpapi_client, repository):
        self.settings = settings
        self.gemini_client = gemini_client
        self.serpapi_client = serpapi_client
        self.repository = repository

    @staticmethod
    def _extract_term(item: dict[str, Any]) -> str | None:
        return item.get("keyword") or item.get("keyword_info", {}).get("keyword") or item.get("term")

    @staticmethod
    def _intent_from_value(value: str | None) -> SearchIntent | None:
        if value is None:
            return None
        return SearchIntent(value)

    async def _expand_with_free_sources(self, payload: KeywordAgentInput) -> list[str]:
        expansion_response = await self.gemini_client.analyze(
            KEYWORD_EXPANSION_PROMPT.format(
                site_description=payload.site_config.get("site_description", ""),
                target_audience=payload.site_config.get("target_audience", ""),
                services=", ".join(payload.site_config.get("services", [])),
                seed_keyword=payload.seed_keyword,
                max_keywords=payload.max_keywords,
            ),
            json.dumps(
                {
                    "seed_keyword": payload.seed_keyword,
                    "site_config": payload.site_config,
                    "max_keywords": payload.max_keywords,
                }
            ),
        )
        expanded_terms = [payload.seed_keyword]
        expanded_terms.extend(
            item["keyword"]
            for item in expansion_response.get("items", [])
            if isinstance(item, dict) and item.get("keyword")
        )

        serp_queries = list(dict.fromkeys(expanded_terms))[: min(5, payload.max_keywords)]
        for term in serp_queries:
            related = await self.serpapi_client.get_related_searches(term, location=self.settings.search_location)
            expanded_terms.extend(related)

        return list(dict.fromkeys(term.strip() for term in expanded_terms if term.strip()))[: payload.max_keywords]

    async def run(self, payload: KeywordAgentInput) -> KeywordAgentOutput:
        metrics: list[dict] = []
        difficulties: list[dict] = []
        source = "gemini_serpapi"
        expanded_terms = await self._expand_with_free_sources(payload)

        metrics_by_term = {
            self._extract_term(item) or "": item for item in metrics if self._extract_term(item)
        }
        difficulty_by_term = {
            self._extract_term(item) or "": item for item in difficulties if self._extract_term(item)
        }
        intent_response = await self.gemini_client.analyze(
            KEYWORD_INTENT_PROMPT.format(
                site_description=payload.site_config.get("site_description", ""),
                keywords_json=json.dumps(expanded_terms),
            ),
            json.dumps(expanded_terms),
        )
        intent_items = intent_response.get("items", intent_response if isinstance(intent_response, list) else [])
        intents_by_term = {item["keyword"]: item["intent"] for item in intent_items if "keyword" in item}

        saved_ids: list[str] = []
        for term in expanded_terms:
            metric = metrics_by_term.get(term, {})
            difficulty = difficulty_by_term.get(term, {})
            monthly_volume = metric.get("search_volume") or metric.get("keyword_info", {}).get("search_volume")
            difficulty_score = difficulty.get("keyword_difficulty") or difficulty.get("difficulty")
            if monthly_volume is not None and monthly_volume < self.settings.min_monthly_volume:
                continue
            if difficulty_score is not None and difficulty_score > self.settings.max_keyword_difficulty:
                continue
            keyword = Keyword(
                term=term,
                seed_keyword=payload.seed_keyword,
                monthly_volume=monthly_volume,
                difficulty_score=int(difficulty_score) if difficulty_score is not None else None,
                cpc_usd=metric.get("cpc"),
                competition_level=metric.get("competition"),
                search_intent=self._intent_from_value(intents_by_term.get(term)),
                source=source,
                lifecycle_status=KeywordLifecycleStatus.DISCOVERED,
                locale=payload.site_config.get("primary_language", "en"),
                market=self.settings.primary_market,
                metrics_source=source,
            )
            saved = self.repository.upsert_keyword(keyword)
            saved_ids.append(saved.id)
        return KeywordAgentOutput(
            seed_keyword=payload.seed_keyword,
            keywords_found=len(expanded_terms),
            keywords_saved=len(saved_ids),
            keyword_ids=saved_ids,
        )
