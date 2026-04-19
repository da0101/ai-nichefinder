# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Feature:** gsc-monitoring
**Status:** in-progress

---

## What we're building

Google Search Console provider client — fetches impressions/clicks/CTR/position from the GSC API and populates `SearchConsoleRecord` rows in SQLite. Exposed via `seo monitor sync` CLI command.

## Why

Real GSC data (impressions, clicks, position) closes the post-publish feedback loop — the pipeline can see whether published articles are actually ranking and feed that back into future scoring decisions.

## What done looks like

- `seo monitor sync` CLI command fetches GSC rows and persists them to `SearchConsoleRecord`.
- Idempotent: re-running doesn't duplicate rows.
- 5+ tests pass; full pytest suite green.
- Manual local verification confirmed.

## Current state

- Phase 1: complete
- Data Model V2: complete and merged to develop
- **Active:** gsc-monitoring (feature/gsc-monitoring branch)
- Next after this: GA4 provider → source registry → LangGraph interrupt/resume

## Relevant context

- `.platform/work/gsc-monitoring.md`
- `.platform/domains/gsc-monitoring.md`
- `.platform/domains/data-architecture.md`
- `packages/core/src/nichefinder_core/models/tracking.py` — SearchConsoleRecord model
- `packages/db/src/nichefinder_db/crud.py` — save_search_console_record / list_search_console_records

**Never load:** `work/archive/*`
