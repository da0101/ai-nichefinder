# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Features:** gsc-monitoring, serp-pipeline-fix, buyer-problem-research, dashboard-rework, reddit-api-integration, google-ads-api-integration, rest-api-control-plane
**Status:** mixed active states (in-progress, blocked, planning)

---

## What we're building

Buyer-problem-first keyword discovery for `danilulmashev.com` — identify real business-owner problems first, then derive article-worthy keywords, and only spend SERP budget on finalists. In parallel, GSC monitoring continues to deepen the post-publish feedback loop.

## Why

The current pipeline still proposes many commercially flavored but unwinnable queries. Starting from buyer problems instead of “hire developer” keywords should produce article opportunities a polished site can realistically compete for, while GSC data provides the first-party feedback needed to refine those choices over time.

## What done looks like

- Research flow can surface structured buyer problems before keyword expansion.
- Keyword shortlists prefer article-fit + business-fit over raw hire-intent phrasing.
- `seo monitor sync` fetches GSC rows into `SearchConsoleRecord` for first-party feedback.
- Full pytest suite green.

## Current state

- Phase 1: complete
- Data Model V2: complete and merged to develop
- **Active:** buyer-problem-research on top of the current keyword-research flow
- Also active: gsc-monitoring, serp-pipeline-fix, dashboard-rework
- Newly tracked: reddit-api-integration (blocked waiting on Reddit approval), google-ads-api-integration (planning)
- REST control-plane is active again: typed local jobs now cover validation, research, brief generation, and article writing, and the API also exposes article/report/budget reads plus approve/publish mutations, with SQLite-persisted job status and loopback-or-token write guards.
- Next after this: GA4 provider → source registry → LangGraph interrupt/resume

## Relevant context

- `.platform/work/gsc-monitoring.md`
- `.platform/work/buyer-problem-research.md`
- `.platform/work/reddit-api-integration.md`
- `.platform/work/google-ads-api-integration.md`
- `.platform/work/rest-api-control-plane.md`
- `.platform/domains/buyer-problem-research.md`
- `.platform/domains/gsc-monitoring.md`
- `.platform/domains/keyword-research.md`
- `.platform/domains/rest-api-control-plane.md`
- `packages/core/src/nichefinder_core/pre_serp.py` — deterministic pre-SERP shortlist scoring
- `.platform/work/dashboard-rework.md`
- `.platform/domains/viewer.md`
- `apps/cli/src/nichefinder_cli/viewer_server.py`
- `apps/dashboard/` — React + shadcn/ui dashboard (new)
- `packages/core/src/nichefinder_core/models/tracking.py` — SearchConsoleRecord model
- `packages/db/src/nichefinder_db/crud.py` — save_search_console_record / list_search_console_records

**Never load:** `work/archive/*`
