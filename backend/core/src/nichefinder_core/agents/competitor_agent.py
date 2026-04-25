import json

from pydantic import BaseModel

from nichefinder_core.gemini.prompts import COMPETITOR_ANALYSIS_PROMPT
from nichefinder_core.models import CompetitorPage
from nichefinder_core.utils.logger import get_logger

logger = get_logger(__name__)


class CompetitorAgentInput(BaseModel):
    keyword_id: str
    serp_result_id: str
    max_pages_to_fetch: int = 3


class CompetitorAgentOutput(BaseModel):
    keyword_id: str
    pages_fetched: int
    avg_word_count: int
    common_h2_topics: list[str]
    questions_covered: list[str]
    content_gaps: list[str]
    recommended_word_count: int
    competitor_page_ids: list[str]


class CompetitorAgent:
    def __init__(self, *, gemini_client, scraper, repository):
        self.gemini_client = gemini_client
        self.scraper = scraper
        self.repository = repository

    async def run(self, payload: CompetitorAgentInput) -> CompetitorAgentOutput:
        serp_result = self.repository.get_latest_serp_result(payload.keyword_id)
        if serp_result is None:
            raise ValueError("SERP result not found")
        pages = json.loads(serp_result.pages_json)
        fetched_pages = []
        competitor_ids: list[str] = []
        for page in pages[: payload.max_pages_to_fetch]:
            try:
                scraped = await self.scraper.fetch_article(page["url"])
            except Exception as exc:
                logger.warning("Skipping competitor page after scrape failure: %s (%s)", page["url"], exc)
                continue
            if scraped is None:
                continue
            fetched_pages.append(scraped.model_dump(mode="json"))
            record = CompetitorPage(
                serp_result_id=payload.serp_result_id,
                url=scraped.url,
                title=scraped.title,
                word_count=scraped.word_count,
                h1=scraped.h1,
                h2_list=json.dumps(scraped.h2_list),
                h3_list=json.dumps(scraped.h3_list),
                questions_answered=json.dumps(scraped.h2_list + scraped.h3_list),
                internal_link_count=len(scraped.internal_links),
                external_link_count=len(scraped.external_links),
                has_schema_markup=scraped.has_schema_markup,
                estimated_reading_time_min=max(1, scraped.word_count // 200),
                content_summary="",
            )
            saved = self.repository.create_competitor_page(record)
            competitor_ids.append(saved.id)
        analysis = await self.gemini_client.analyze(
            COMPETITOR_ANALYSIS_PROMPT.format(
                keyword=self.repository.get_keyword(payload.keyword_id).term,
                pages_json=json.dumps(fetched_pages),
            ),
            json.dumps(fetched_pages),
        )
        avg_word_count = (
            int(sum(item["word_count"] for item in fetched_pages) / len(fetched_pages))
            if fetched_pages
            else 0
        )
        return CompetitorAgentOutput(
            keyword_id=payload.keyword_id,
            pages_fetched=len(fetched_pages),
            avg_word_count=avg_word_count,
            common_h2_topics=analysis.get("table_stakes_topics", []),
            questions_covered=analysis.get("questions_answered", []),
            content_gaps=analysis.get("gap_opportunities", []),
            recommended_word_count=analysis.get("recommended_word_count", int(avg_word_count * 1.2)),
            competitor_page_ids=competitor_ids,
        )
