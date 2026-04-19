# Architecture

## Current Scope

The codebase is a local, CLI-first SEO research and content workflow for
`danilulmashev.com`. It coordinates keyword discovery, SERP and competitor
analysis, deterministic opportunity scoring, Gemini-backed synthesis, article
generation, and rank tracking without introducing a web surface.

## Package Boundaries

- `nichefinder-core`
  - Settings and site config
  - SQLModel-backed domain models
  - Gemini client and prompts
  - Source clients, atomic agents, and LangGraph workflow definitions
- `nichefinder-db`
  - SQLite engine/session handling
  - CRUD and analytics queries
  - Alembic environment
- `nichefinder-cli`
  - Operator commands
  - Runtime/service wiring
  - Interactive config, research, content, budget, and rank workflows

## Persistence

- Primary database: SQLite at `data/db/seo.db`
- Generated drafts: `outputs/articles/`
- Reports: `outputs/reports/`
- Audits: `outputs/audits/`
- Site-specific context: `data/site_config.json`

## AI and Orchestration

- Gemini provider: `google-genai`
- Analytical model default: `gemini-2.0-flash`
- Content-writing model default: `gemini-2.0-pro`
- Workflow engine: LangGraph `StateGraph`
- Human checkpoints happen before content creation and before final approval

## Scoring Direction

- Opportunity score is deterministic before any LLM synthesis
- Weighted inputs: volume, inverted difficulty, trend, intent, and competition
- If SERP rankability is false, the score is capped at 40
