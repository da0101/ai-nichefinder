from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.keyword_agent import KeywordAgent, KeywordAgentInput
from nichefinder_core.models import KeywordLifecycleStatus
from nichefinder_core.settings import Settings
from nichefinder_db.crud import SeoRepository

class FakeSerpAPIClient:
    async def get_related_searches(self, keyword: str, location: str = "Montreal, Quebec, Canada"):
        return []


class FakeGeminiClient:
    async def analyze(self, system_prompt: str, user_content: str):
        if "Generate long-tail keyword ideas" in system_prompt:
            return {
                "items": [
                    {"keyword": "ai consultant for startups"},
                    {"keyword": "hire ai consultant"},
                ]
            }
        return {
            "items": [
                {"keyword": "high value keyword", "intent": "commercial"},
                {"keyword": "low volume keyword", "intent": "informational"},
                {"keyword": "ai consultant", "intent": "commercial"},
                {"keyword": "ai consultant for startups", "intent": "commercial"},
                {"keyword": "hire ai consultant", "intent": "commercial"},
                {"keyword": "ai strategy consultant", "intent": "commercial"},
            ]
        }


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


class FreeTierSerpAPIClient:
    async def get_related_searches(self, keyword: str, location: str = "Montreal, Quebec, Canada"):
        related = {
            "ai consultant": ["ai strategy consultant", "ai consultant pricing"],
            "ai consultant for startups": ["startup ai consultant"],
            "hire ai consultant": ["best ai consultant for business"],
        }
        return related.get(keyword, [])


async def test_keyword_agent_creates_keywords_from_gemini_and_serpapi_sources():
    repository = _repository()
    settings = Settings(
        min_monthly_volume=100,
        max_keyword_difficulty=50,
    )
    agent = KeywordAgent(
        settings=settings,
        gemini_client=FakeGeminiClient(),
        serpapi_client=FreeTierSerpAPIClient(),
        repository=repository,
    )
    output = await agent.run(
        KeywordAgentInput(
            seed_keyword="ai consultant",
            site_config={
                "site_description": "AI development consultancy",
                "target_audience": "startup founders",
                "services": ["AI consulting", "AI development"],
                "primary_language": "en",
            },
            max_keywords=10,
        )
    )
    keywords = repository.list_keywords()
    terms = {keyword.term for keyword in keywords}
    assert output.keywords_saved >= 3
    assert "ai consultant" in terms
    assert "ai consultant for startups" in terms
    assert "ai strategy consultant" in terms
    assert all(keyword.source == "gemini_serpapi" for keyword in keywords)
    assert all(keyword.lifecycle_status == KeywordLifecycleStatus.DISCOVERED for keyword in keywords)
    assert all(keyword.locale == "en" for keyword in keywords)
    assert all(keyword.market == "North America" for keyword in keywords)
    assert all(keyword.metrics_source == "gemini_serpapi" for keyword in keywords)
