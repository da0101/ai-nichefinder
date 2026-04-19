from pathlib import Path

from typer.testing import CliRunner

from nichefinder_cli.main import app
from nichefinder_core.models import Article, ContentType, Keyword
from nichefinder_core.settings import Settings
from nichefinder_db import SeoRepository, create_db_and_tables, get_session


def _seed_article(tmp_path: Path, status: str) -> tuple[Settings, str]:
    db_path = tmp_path / "seo.db"
    settings = Settings(database_url=f"sqlite:///{db_path}")
    create_db_and_tables(settings)
    with get_session(settings) as session:
        repository = SeoRepository(session)
        keyword = repository.upsert_keyword(
            Keyword(term="ai consultant", seed_keyword="ai consultant", source="manual")
        )
        article = repository.create_article(
            Article(
                keyword_id=keyword.id,
                title="AI Consultant Guide",
                slug="ai-consultant-guide",
                content_type=ContentType.HOW_TO,
                status=status,
                word_count=1000,
                file_path=str(tmp_path / "article.md"),
            ),
            "# Draft",
        )
        article_id = article.id
    return settings, article_id


def test_publish_requires_approved_article(monkeypatch, tmp_path: Path):
    settings, article_id = _seed_article(tmp_path, status="draft")
    monkeypatch.setattr(
        "nichefinder_cli.main.get_runtime",
        lambda: (settings, None, get_session(settings)),
    )

    result = CliRunner().invoke(app, ["publish", article_id, "https://example.com/post"])

    assert result.exit_code == 1
    assert "must be approved before it can be published" in result.output


def test_publish_marks_approved_article_as_published(monkeypatch, tmp_path: Path):
    settings, article_id = _seed_article(tmp_path, status="approved")
    monkeypatch.setattr(
        "nichefinder_cli.main.get_runtime",
        lambda: (settings, None, get_session(settings)),
    )

    result = CliRunner().invoke(app, ["publish", article_id, "https://example.com/post"])

    assert result.exit_code == 0
    with get_session(settings) as session:
        repository = SeoRepository(session)
        article = repository.get_article(article_id)
        assert article is not None
        assert article.status == "published"
        assert article.published_url == "https://example.com/post"
