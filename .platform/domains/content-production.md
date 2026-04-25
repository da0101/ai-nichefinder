---
domain_id: dom-content-production
slug: content-production
status: active
repo_ids: [repo-primary]
related_domain_slugs: [keyword-research, rank-tracking]
created_at: 2026-04-17
updated_at: 2026-04-19
---

# content-production

## What this domain does

Turns vetted opportunities into content briefs, draft articles, and rewrites that the operator can review before publication. This domain exists to help produce useful blog content faster without losing judgment about whether the topic is worth publishing.

## Backend / source of truth

- `ContentBrief`, `ContentBriefRecord`, `Article`, and `ArticleVersion` store the planning and draft lifecycle.
- `generate_brief`, `write_article`, and `rewrite_article` orchestrate the main content workflows.
- `ContentAgent`, `CompetitorAgent`, and `SynthesisAgent` assemble structure, competing URLs, gaps, and generated copy.
- `SeoRepository` stores briefs, articles, approvals, publish state, and versioned article content.

## Frontend / clients

- `nichefinder brief <keyword-id>` generates a brief for a researched keyword.
- `nichefinder write <keyword-id>` drafts a new article from the latest brief.
- `nichefinder rewrite <url>` scrapes an existing article and produces a rewrite-oriented brief and draft.
- `nichefinder articles list`, `articles approve`, and `publish` manage human checkpoints and publication state.
- `nichefinder view` exposes the latest brief and article preview for inspection without leaving the local machine.

## API contract locked

- Human review remains in the loop before publication.
- Rewrites must preserve the source URL and mark the brief/article as rewrite-oriented.
- Content generation should consume normalized brief data rather than raw provider payloads.

## Key files

- `backend/apps/cli/src/nichefinder_cli/main.py`
- `backend/apps/cli/src/nichefinder_cli/commands/articles.py`
- `backend/apps/cli/src/nichefinder_cli/workflows.py`
- `backend/core/src/nichefinder_core/agents/content_agent.py`
- `backend/core/src/nichefinder_core/agents/competitor_agent.py`
- `backend/core/src/nichefinder_core/agents/synthesis_agent.py`
- `backend/core/src/nichefinder_core/models/content.py`
- `backend/core/src/nichefinder_core/sources/scraper.py`
- `backend/db/src/nichefinder_db/crud.py`

## Decisions locked

- The goal is rank-aware usefulness, not bulk AI text generation.
- Article drafts are not production-ready by default.
- Scraping for rewrites or competitor inspection must obey robots and rate limits.
- Filesystem outputs and DB records should stay in sync enough that a draft can be inspected outside the database.
