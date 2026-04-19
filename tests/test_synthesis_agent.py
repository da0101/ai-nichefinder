from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.synthesis_agent import SynthesisAgent, SynthesisAgentInput
from nichefinder_core.models import Keyword, KeywordLifecycleStatus, SearchIntent
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
    score_record = repository.get_latest_opportunity_score(keyword.id)
    assert score_record is not None
    assert score_record.formula_version == "opportunity_v2"
    updated_keyword = repository.get_keyword(keyword.id)
    assert updated_keyword is not None
    assert updated_keyword.lifecycle_status == KeywordLifecycleStatus.ANALYZED


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
    score_record = repository.get_latest_opportunity_score(keyword.id)
    assert score_record is not None
    assert score_record.action == "new_article"
    updated_keyword = repository.get_keyword(keyword.id)
    assert updated_keyword is not None
    assert updated_keyword.lifecycle_status == KeywordLifecycleStatus.TARGETED
    assert updated_keyword.score_formula_version == "opportunity_v2"


async def test_synthesis_uses_avg_interest_as_volume_proxy():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="custom web development",
            seed_keyword="custom web development",
            search_intent=SearchIntent.COMMERCIAL,
            source="gemini_serpapi",
            # no monthly_volume — simulates free-source keyword
        )
    )
    gemini = FakeGeminiClient()
    agent = SynthesisAgent(settings=Settings(min_opportunity_score=60), gemini_client=gemini, repository=repository)

    output = await agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config={},
            keyword_data={},
            serp_data={"competition_level": "low", "rankable": True, "avg_interest": 0},
            trend_data={"direction": "rising", "avg_interest": 0.0},
            ads_data={},
            competitor_data={"avg_word_count": 1000, "content_gaps": [], "recommended_word_count": 1200},
        )
    )
    # avg_interest=0 → volume_score=0, not the neutral 60 fallback
    assert output.opportunity_score.volume_score == 0.0


async def test_synthesis_uses_difficulty_estimate_from_serp():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="react developer for hire",
            seed_keyword="react developer for hire",
            search_intent=SearchIntent.COMMERCIAL,
            source="gemini_serpapi",
            # no difficulty_score — will use serp estimate
        )
    )
    gemini = FakeGeminiClient()
    agent = SynthesisAgent(settings=Settings(min_opportunity_score=60), gemini_client=gemini, repository=repository)

    output = await agent.run(
        SynthesisAgentInput(
            keyword_id=keyword.id,
            site_config={},
            keyword_data={},
            # difficulty_estimate=30 → difficulty_score = 100 - 30 = 70
            serp_data={"competition_level": "medium", "rankable": True, "difficulty_estimate": 30},
            trend_data={"direction": "stable", "avg_interest": 60.0},
            ads_data={},
            competitor_data={"avg_word_count": 1000, "content_gaps": [], "recommended_word_count": 1200},
        )
    )
    assert output.opportunity_score.difficulty_score == 70.0
    # volume from avg_interest=60 → volume_score=60
    assert output.opportunity_score.volume_score == 60.0


async def test_synthesis_high_interest_high_difficulty_scores_correctly():
    repository = _repository()
    keyword = repository.upsert_keyword(
        Keyword(
            term="web developer canada",
            seed_keyword="web developer canada",
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
            # SERP: wikipedia + reddit in top 5 + PAA → difficulty_estimate ~40
            # avg_interest 75 → volume_score 75
            serp_data={"competition_level": "high", "rankable": True, "difficulty_estimate": 40},
            trend_data={"direction": "stable", "avg_interest": 75.0},
            ads_data={},
            competitor_data={"avg_word_count": 1500, "content_gaps": [], "recommended_word_count": 1800},
        )
    )
    # volume: 75, difficulty: 60 (100-40), trend: 50 (stable), intent: 80 (commercial), competition: 10 (high)
    # composite = 75*0.25 + 60*0.30 + 50*0.20 + 80*0.15 + 10*0.10
    #           = 18.75 + 18.0 + 10.0 + 12.0 + 1.0 = 59.75
    assert output.opportunity_score.volume_score == 75.0
    assert output.opportunity_score.difficulty_score == 60.0
    assert output.opportunity_score.composite_score == 59.75


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
