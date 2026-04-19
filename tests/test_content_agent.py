from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from nichefinder_core.agents.content_agent import ContentAgent, ContentAgentInput
from nichefinder_core.models import ContentBrief, ContentType, Keyword
from nichefinder_core.settings import Settings
from nichefinder_db.crud import SeoRepository


class FakeGeminiClient:
    def __init__(self):
        self.last_prompt = ""

    async def write(self, system_prompt: str, content_brief: str) -> str:
        self.last_prompt = system_prompt
        return "# AI Consultant Guide\n\nThis article explains how to hire an AI consultant effectively."


def _repository():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    return SeoRepository(session)


async def test_content_agent_creates_markdown_file_and_article_record(tmp_path: Path):
    repository = _repository()
    keyword = repository.upsert_keyword(Keyword(term="ai consultant", seed_keyword="ai consultant", source="manual"))
    settings = Settings(
        articles_dir=tmp_path / "articles",
        content_templates_dir=Path("/Users/danilulmashev/Documents/GitHub/ai-nichefinder/data/content_templates"),
    )
    gemini = FakeGeminiClient()
    agent = ContentAgent(settings=settings, gemini_client=gemini, repository=repository)
    brief = ContentBrief(
        target_keyword="ai consultant",
        secondary_keywords=["hire ai consultant"],
        content_type=ContentType.HOW_TO,
        suggested_title="AI Consultant Guide",
        suggested_h2_structure=["Why hire one", "How to choose"],
        questions_to_answer=["What does one cost?"],
        word_count_target=1200,
        tone="technical",
        cta_type="contact_form",
        competing_urls=[],
        is_rewrite=True,
        existing_article_url="https://example.com/old",
        existing_article_content="Old content",
    )
    output = await agent.run(
        ContentAgentInput(content_brief=brief, site_config={"site_name": "Daniil Ulmashev"}, existing_content="Old content"),
        keyword_id=keyword.id,
    )
    assert Path(output.file_path).exists()
    assert repository.get_article(output.article_id).status == "draft"
    assert "REWRITE INSTRUCTION" in gemini.last_prompt
