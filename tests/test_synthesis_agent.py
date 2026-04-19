from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.synthesis_agent import SynthesisAgent, SynthesisAgentInput
from nichefinder_core.models import Keyword, SearchIntent
from nichefinder_core.settings import Settings
from nichefinder_db.crud import SeoRepository


class FakeGeminiClient:
    def __init__(self):
        self.called = False

    async def analyze(self, system_prompt: str, user_content: str):
        self.called = True
        return {
            "why_good_fit": "Strong fit.",
            "content_type": "how_to",
            "suggested_title": "How to hire an AI consultant",
            "suggested_h2_structure": ["What to look for", "Cost", "Process"],
            "questions_to_answer": ["How much does it cost?"],
            "secondary_keywords": ["ai consultant services"],
            "tone": "technical",
            "cta_type": "contact_form",
            "action": "new_article",
            "existing_article_url": None,
        }


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


async def test_synthesis_formula_and_rankable_cap():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="ai consultant",
            seed_keyword="ai consultant",
            monthly_volume=1000,
            difficulty_score=10,
            search_intent=SearchIntent.COMMERCIAL,
            source="manual",
        )
    )
    gemini = FakeGeminiClient()
    agent = SynthesisAgent(settings=Settings(min_opportunity_score=60), gemini_client=gemini, repository=repository)
    output = await agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config={},
            keyword_data={},
            serp_data={"competition_level": "low", "rankable": False},
            trend_data={"direction": "rising"},
            ads_data={},
            competitor_data={"avg_word_count": 1000, "content_gaps": [], "recommended_word_count": 1200},
        )
    )
    assert output.opportunity_score.composite_score == 40.0
    assert output.should_create_content is False
    assert gemini.called is False


async def test_synthesis_uses_neutral_fallback_scores_for_free_source_keywords():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="custom ai tool development for small business",
            seed_keyword="custom ai tool development for small business",
            search_intent=SearchIntent.COMMERCIAL,
            source="gemini_serpapi",
        )
    )
    gemini = FakeGeminiClient()
    agent = SynthesisAgent(settings=Settings(min_opportunity_score=60), gemini_client=gemini, repository=repository)

    output = await agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config={},
            keyword_data={},
            serp_data={"competition_level": "medium", "rankable": True, "paa_questions": []},
            trend_data={"direction": "stable"},
            ads_data={},
            competitor_data={"avg_word_count": 1000, "content_gaps": [], "recommended_word_count": 1200},
        )
    )

    assert output.opportunity_score.volume_score == 60.0
    assert output.opportunity_score.difficulty_score == 60.0
    assert output.opportunity_score.composite_score == 60.0
    assert output.should_create_content is True
    assert output.content_brief is not None
    assert gemini.called is True


async def test_synthesis_keeps_non_free_source_unknown_metrics_conservative():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="manual keyword with no metrics",
            seed_keyword="manual keyword with no metrics",
            search_intent=SearchIntent.COMMERCIAL,
            source="manual",
        )
    )
    gemini = FakeGeminiClient()
    agent = SynthesisAgent(settings=Settings(min_opportunity_score=60), gemini_client=gemini, repository=repository)

    output = await agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config={},
            keyword_data={},
            serp_data={"competition_level": "medium", "rankable": True, "paa_questions": []},
            trend_data={"direction": "stable"},
            ads_data={},
            competitor_data={"avg_word_count": 1000, "content_gaps": [], "recommended_word_count": 1200},
        )
    )

    assert output.opportunity_score.volume_score == 0.0
    assert output.opportunity_score.difficulty_score == 0.0
    assert output.should_create_content is False
    assert output.content_brief is None
    assert gemini.called is False
