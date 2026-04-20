import json
import re
from typing import Any

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import (
    BUYER_PROBLEM_DISCOVERY_PROMPT,
    KEYWORD_INTENT_PROMPT,
    PROBLEM_KEYWORD_EXPANSION_PROMPT,
)
from nichefinder_core.models import BuyerProblem, Keyword, KeywordLifecycleStatus, SearchIntent
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
    buyer_problems: list[BuyerProblem]


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

    def _recent_query_evidence(self, seed_keyword: str, limit: int = 8) -> list[str]:
        seed_tokens = {token for token in re.findall(r"[a-z0-9]+", seed_keyword.lower()) if len(token) > 2}
        records = self.repository.list_search_console_records(limit=50)
        matches: list[str] = []
        seen: set[str] = set()
        for record in records:
            query = record.query.strip()
            query_tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
            if query.lower() in seen:
                continue
            if seed_tokens and not (seed_tokens & query_tokens):
                continue
            seen.add(query.lower())
            matches.append(query)
            if len(matches) >= limit:
                break
        return matches

    async def _discover_buyer_problems(self, payload: KeywordAgentInput) -> list[BuyerProblem]:
        evidence_queries = self._recent_query_evidence(payload.seed_keyword)
        response = await self.gemini_client.analyze(
            BUYER_PROBLEM_DISCOVERY_PROMPT.format(
                site_description=payload.site_config.get("site_description", ""),
                target_audience=payload.site_config.get("target_audience", ""),
                services=", ".join(payload.site_config.get("services", [])),
                seed_keyword=payload.seed_keyword,
                evidence_queries_json=json.dumps(evidence_queries),
                max_problems=min(8, payload.max_keywords),
            ),
            json.dumps(
                {
                    "seed_keyword": payload.seed_keyword,
                    "site_config": payload.site_config,
                    "evidence_queries": evidence_queries,
                }
            ),
        )
        items = response.get("items", response if isinstance(response, list) else [])
        return [BuyerProblem.model_validate(item) for item in items if isinstance(item, dict) and item.get("problem")]

    async def _expand_with_free_sources(
        self, payload: KeywordAgentInput
    ) -> tuple[list[str], list[BuyerProblem]]:
        buyer_problems = await self._discover_buyer_problems(payload)
        expansion_response = await self.gemini_client.analyze(
            PROBLEM_KEYWORD_EXPANSION_PROMPT.format(
                buyer_problems_json=json.dumps([problem.model_dump() for problem in buyer_problems]),
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
                    "buyer_problems": [problem.model_dump() for problem in buyer_problems],
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

        return (
            list(dict.fromkeys(term.strip() for term in expanded_terms if term.strip()))[: payload.max_keywords],
            buyer_problems,
        )

    async def run(self, payload: KeywordAgentInput) -> KeywordAgentOutput:
        metrics: list[dict] = []
        difficulties: list[dict] = []
        source = "gemini_serpapi"
        expanded_terms, buyer_problems = await self._expand_with_free_sources(payload)

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
            buyer_problems=buyer_problems,
        )
