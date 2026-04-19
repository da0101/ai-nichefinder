import json
from datetime import date

import httpx
from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.serp_agent import SerpAgent, SerpAgentInput
from nichefinder_core.models import Keyword
from nichefinder_core.settings import Settings
from nichefinder_core.sources.serpapi import SerpAPIClient
from nichefinder_db.crud import SeoRepository


class FakeGeminiClient:
    async def analyze(self, system_prompt: str, user_content: str):
        return {"competition_level": "medium", "rankable": True}


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


async def test_serp_agent_persists_result_and_pages():
    repository = _repository()
    keyword = repository.upsert_keyword(Keyword(term="ai consultant", seed_keyword="ai consultant", source="manual"))
    payload = {
        "organic_results": [{"position": 1, "title": "Page", "link": "https://example.com", "snippet": "Snippet"}],
        "people_also_ask": [{"question": "What does an AI consultant do?"}],
    }

    class FakeSerpClient:
        async def search(self, keyword: str, location: str = "United States", num_results: int = 10):
            return payload

        @staticmethod
        def parse_search_response(payload: dict):
            return SerpAPIClient.parse_search_response(payload)

    agent = SerpAgent(gemini_client=FakeGeminiClient(), serpapi_client=FakeSerpClient(), repository=repository)
    output = await agent.run(SerpAgentInput(keyword_id=keyword.id, keyword_term=keyword.term))
    stored = repository.get_latest_serp_result(keyword.id)
    assert output.pages_analyzed == 1
    assert stored is not None
    assert json.loads(stored.pages_json)[0]["url"] == "https://example.com"


async def test_serpapi_monthly_counter_increments_and_blocks(monkeypatch):
    repository = _repository()
    settings = Settings(serpapi_key="token", serpapi_calls_per_month=1)
    client = SerpAPIClient(settings, repository)
    payload = {"organic_results": []}

    async def fake_get(*args, **kwargs):
        return FakeResponse(payload)

    monkeypatch.setattr(client.client, "get", fake_get)
    await client.search("first keyword")
    usage = repository.get_api_usage("serpapi", date.today().replace(day=1))
    assert usage is not None
    assert usage.call_count == 1
    try:
        await client.search("second keyword")
        raised = False
    except RuntimeError:
        raised = True
    assert raised is True
