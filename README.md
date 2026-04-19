# AI Nichefinder

Personal AI-powered SEO research and content strategy tooling for `danilulmashev.com`.

## What It Does

- Expands seed keywords into qualified opportunities
- Analyzes SERPs, trends, ad signals, and competitor content
- Computes deterministic opportunity scores before any LLM synthesis
- Generates content briefs and draft articles with Gemini
- Tracks generated content, approvals, publishing state, and ranking snapshots

## Stack

- Python 3.12
- Typer CLI
- LangGraph
- Google Gemini via `google-genai`
- SQLModel + SQLite
- httpx, pytrends, Playwright, BeautifulSoup, readability-lxml
- Jinja2, Rich, python-frontmatter, tenacity

## Quick Start

1. Copy `.env.example` to `.env`
2. Install dependencies:

```bash
uv sync
```

3. Create the local database:

```bash
uv run --package nichefinder-cli seo db init
```

4. Inspect current configuration:

```bash
uv run --package nichefinder-cli seo status
```

5. Update `data/site_config.json` interactively if needed:

```bash
uv run --package nichefinder-cli seo config
```

## Main Commands

```bash
uv run --package nichefinder-cli seo research "ai development consultant"
uv run --package nichefinder-cli seo research-batch
uv run --package nichefinder-cli seo keywords list
uv run --package nichefinder-cli seo brief <keyword-id>
uv run --package nichefinder-cli seo write <keyword-id>
uv run --package nichefinder-cli seo rewrite https://danilulmashev.com/en/blog/example/
uv run --package nichefinder-cli seo articles list
uv run --package nichefinder-cli seo articles approve <article-id>
uv run --package nichefinder-cli seo publish <article-id> https://danilulmashev.com/en/blog/new-post/
uv run --package nichefinder-cli seo rank check
uv run --package nichefinder-cli seo report
uv run --package nichefinder-cli seo budget
```

## Important Constraints

- Gemini only. No OpenAI or Claude integration.
- Local persistence only. SQLite and filesystem store the project state.
- Human approval is expected before generated content is treated as final.
- SerpAPI is the only Google SERP source. No direct Google Search scraping.
- DataForSEO is not part of the active pipeline.
