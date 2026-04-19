import re
from datetime import datetime, timezone
from pathlib import Path

import frontmatter
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from nichefinder_core.gemini.prompts import CONTENT_GENERATION_PROMPT
from nichefinder_core.models import Article, ContentBrief
from nichefinder_core.settings import Settings


class ContentAgentInput(BaseModel):
    content_brief: ContentBrief
    site_config: dict
    existing_content: str | None = None


class ContentAgentOutput(BaseModel):
    article_id: str
    file_path: str
    word_count: int
    title: str
    meta_description: str
    slug: str


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "article"


def _extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _derive_meta_description(markdown: str, target_keyword: str) -> str:
    body = " ".join(line.strip() for line in markdown.splitlines() if line and not line.startswith("#"))
    description = body[:157].rsplit(" ", 1)[0]
    if target_keyword.lower() not in description.lower():
        description = f"{target_keyword}: {description}"
    return description[:160]


class ContentAgent:
    def __init__(self, *, settings: Settings, gemini_client, repository):
        self.settings = settings
        self.gemini_client = gemini_client
        self.repository = repository
        self.environment = Environment(loader=FileSystemLoader(settings.resolved_templates_dir))

    async def run(self, payload: ContentAgentInput, keyword_id: str) -> ContentAgentOutput:
        template_name = f"{payload.content_brief.content_type.value}.md.jinja"
        template = self.environment.get_template(template_name)
        template_hint = template.render(
            title=payload.content_brief.suggested_title,
            target_keyword=payload.content_brief.target_keyword,
            h2_structure=payload.content_brief.suggested_h2_structure,
        )
        rewrite_instruction = ""
        if payload.content_brief.is_rewrite:
            existing = payload.existing_content or payload.content_brief.existing_article_content or ""
            rewrite_instruction = (
                "REWRITE INSTRUCTION: You are rewriting an existing article. "
                "Keep unique insights, improve structure and keyword optimization.\n"
                f"EXISTING ARTICLE:\n{existing}"
            )
        prompt = CONTENT_GENERATION_PROMPT.format(
            author_name=payload.site_config.get("site_name", "Daniil Ulmashev"),
            word_count_target=payload.content_brief.word_count_target,
            content_type=payload.content_brief.content_type.value,
            target_keyword=payload.content_brief.target_keyword,
            secondary_keywords=", ".join(payload.content_brief.secondary_keywords),
            suggested_title=payload.content_brief.suggested_title,
            h2_structure=payload.content_brief.suggested_h2_structure,
            questions_to_answer=payload.content_brief.questions_to_answer,
            tone=payload.content_brief.tone,
            cta_type=payload.content_brief.cta_type,
            rewrite_instruction=rewrite_instruction,
        )
        markdown = await self.gemini_client.write(prompt, template_hint)
        title = _extract_title(markdown, payload.content_brief.suggested_title)
        slug = _slugify(title)
        word_count = len(markdown.split())
        meta_description = _derive_meta_description(markdown, payload.content_brief.target_keyword)
        post = frontmatter.Post(
            markdown,
            title=title,
            date=datetime.now(timezone.utc).date().isoformat(),
            slug=slug,
            target_keyword=payload.content_brief.target_keyword,
            secondary_keywords=payload.content_brief.secondary_keywords,
            meta_description=meta_description,
            word_count=word_count,
            content_type=payload.content_brief.content_type.value,
            status="draft",
        )
        file_path = self.settings.resolved_articles_dir / f"{slug}.md"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(frontmatter.dumps(post), encoding="utf-8")
        article = Article(
            keyword_id=keyword_id,
            title=title,
            slug=slug,
            content_type=payload.content_brief.content_type,
            status="draft",
            word_count=word_count,
            file_path=str(file_path),
            is_rewrite=payload.content_brief.is_rewrite,
            original_url=payload.content_brief.existing_article_url,
        )
        saved = self.repository.create_article(article, frontmatter.dumps(post))
        return ContentAgentOutput(
            article_id=saved.id,
            file_path=str(file_path),
            word_count=word_count,
            title=title,
            meta_description=meta_description,
            slug=slug,
        )
