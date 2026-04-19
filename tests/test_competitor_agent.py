from datetime import datetime, timezone

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.competitor_agent import CompetitorAgent, CompetitorAgentInput
from nichefinder_core.models import Keyword, SerpResult
from nichefinder_core.sources.scraper import ScrapedContent
from nichefinder_db.crud import SeoRepository


class FakeGeminiClient:
    async def analyze(self, system_prompt: str, user_content: str):
        return {
            "table_stakes_topics": ["pricing", "build process"],
            "questions_answered": ["How much does it cost?"],
            "gap_opportunities": ["implementation timeline"],
            "recommended_word_count": 1400,
        }


class FakeScraper:
    async def fetch_article(self, url: str):
        return ScrapedContent(
            url=url,
            title="Example article",
            h1="Example article",
            h2_list=["Pricing", "Build process"],
            h3_list=["Timeline"],
            clean_text="Useful content",
            word_count=900,
            internal_links=[],
            external_links=[],
            has_schema_markup=True,
            fetched_at=datetime.now(timezone.utc),
        )


class FlakyScraper:
    def __init__(self):
        self.calls = 0

    async def fetch_article(self, url: str):
        self.calls += 1
        if self.calls == 1:
            raise TimeoutError("page timed out")
        return await FakeScraper().fetch_article(url)


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


async def test_competitor_agent_handles_scraped_datetime_payloads():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(term="ai tool development", seed_keyword="ai tool development", source="manual")
    )
    serp_result = repository.create_serp_result(
        SerpResult(
            keyword_id=keyword.id,
            features_json="{}",
            pages_json='[{"url":"https://example.com/post","position":1,"title":"Example","domain":"example.com","snippet":"Snippet","content_type":null}]',
            competition_analysis="{}",
            raw_json="{}",
        )
    )

    agent = CompetitorAgent(
        gemini_client=FakeGeminiClient(),
        scraper=FakeScraper(),
        repository=repository,
    )

    output = await agent.run(
        CompetitorAgentInput(keyword_id=keyword.id, serp_result_id=serp_result.id)
    )

    assert output.pages_fetched == 1
    assert output.recommended_word_count == 1400
    assert output.content_gaps == ["implementation timeline"]


async def test_competitor_agent_skips_pages_that_raise_scrape_errors():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(term="ai tool development", seed_keyword="ai tool development", source="manual")
    )
    serp_result = repository.create_serp_result(
        SerpResult(
            keyword_id=keyword.id,
            features_json="{}",
            pages_json='[{"url":"https://example.com/slow","position":1,"title":"Slow","domain":"example.com","snippet":"Snippet","content_type":null},{"url":"https://example.com/post","position":2,"title":"Example","domain":"example.com","snippet":"Snippet","content_type":null}]',
            competition_analysis="{}",
            raw_json="{}",
        )
    )

    agent = CompetitorAgent(
        gemini_client=FakeGeminiClient(),
        scraper=FlakyScraper(),
        repository=repository,
    )

    output = await agent.run(
        CompetitorAgentInput(keyword_id=keyword.id, serp_result_id=serp_result.id)
    )

    assert output.pages_fetched == 1
    assert output.competitor_page_ids
