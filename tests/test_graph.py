from __future__ import annotations

from types import SimpleNamespace

from nichefinder_core.models import BuyerProblem, Keyword, SearchIntent
from nichefinder_core.orchestrator.graph import build_graph
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


class _ModelDump:
    def __init__(self, payload: dict):
        self._payload = payload

    def model_dump(self, mode: str | None = None):
        return self._payload


class _SynthesisOutput:
    def __init__(self, keyword_id: str, keyword_term: str):
        self.opportunity_score = _ModelDump(
            {
                "keyword_id": keyword_id,
                "keyword_term": keyword_term,
                "composite_score": 60.0,
            }
        )
        self.content_brief = None
        self.should_create_content = False
        self.priority_rank = 1

    def model_dump(self, mode: str | None = None):
        return {
            "opportunity_score": self.opportunity_score.model_dump(),
            "content_brief": None,
            "should_create_content": False,
            "priority_rank": 1,
        }


async def test_parallel_analysis_only_uses_selected_shortlist_ids(tmp_path, monkeypatch):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'seo.db'}",
        max_serp_keywords=2,
        tavily_api_key="",
        ddgs_enabled=False,
        bing_enabled=False,
        yahoo_enabled=False,
    )
    create_db_and_tables(settings)

    with get_session(settings) as session:
        repository = SeoRepository(session)
        keywords = [
            repository.upsert_keyword(
                Keyword(
                    term=f"keyword {index}",
                    seed_keyword="seed",
                    source="test",
                    search_intent=SearchIntent.COMMERCIAL,
                )
            )
            for index in range(3)
        ]

        analyzed: list[str] = []
        captured_max_keywords: list[int] = []

        async def fake_shortlist(keyword_ids, repo, trend_agent, *, site_config, location, max_keywords, noise_profile=None):
            captured_max_keywords.append(max_keywords)
            return [
                SimpleNamespace(keyword_id=keywords[0].id, selected=True),
                SimpleNamespace(keyword_id=keywords[1].id, selected=False),
                SimpleNamespace(keyword_id=keywords[2].id, selected=True),
            ]

        class KeywordAgent:
            async def run(self, payload):
                return SimpleNamespace(
                    keyword_ids=[keyword.id for keyword in keywords],
                    buyer_problems=[
                        BuyerProblem(
                            problem="Pricing confusion",
                            audience="owners",
                            why_now="budgeting",
                            article_angle="pricing guide",
                            keyword_seed="website cost montreal",
                            evidence_queries=[],
                        )
                    ],
                )

        class SerpAgent:
            async def run(self, payload):
                analyzed.append(payload.keyword_id)
                return _ModelDump(
                    {
                        "serp_result_id": f"serp-{payload.keyword_id}",
                        "competition_level": "medium",
                        "rankable": False,
                        "difficulty_estimate": 40,
                    }
                )

        class TrendAgent:
            async def run(self, payload):
                return _ModelDump({"direction": "stable", "avg_interest": 50.0})

        class AdsAgent:
            async def run(self, payload):
                return _ModelDump({})

        class SynthesisAgent:
            async def run(self, payload):
                keyword = repository.get_keyword(payload.keyword_id)
                return _SynthesisOutput(payload.keyword_id, keyword.term)

        services = {
            "settings": settings,
            "repository": repository,
            "keyword_agent": KeywordAgent(),
            "serp_agent": SerpAgent(),
            "trend_agent": TrendAgent(),
            "ads_agent": AdsAgent(),
            "synthesis_agent": SynthesisAgent(),
            "competitor_agent": SimpleNamespace(),
        }

        monkeypatch.setattr(
            "nichefinder_core.orchestrator.graph.build_trend_assisted_shortlist",
            fake_shortlist,
        )

        graph = build_graph(services)
        result = await graph.ainvoke({"seed_keywords": ["seed"], "site_config": {}})

    assert captured_max_keywords == [2]
    assert analyzed == [keywords[0].id, keywords[2].id]
    assert set(result["keyword_analyses"]) == {keywords[0].id, keywords[2].id}
