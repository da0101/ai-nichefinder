# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Feature:** _none active_
**Status:** ready for next stream

---

## What we're building

No active stream. Data Model V2 is complete and merged to `develop`.

## Why

The V2 schema and scoring signals are the required foundation before adding GSC/GA4 provider clients, source registry, and deeper orchestration.

## What done looks like

Next logical stream: `gsc-monitoring` — implement the Google Search Console provider client that populates `SearchConsoleRecord` rows, closing the post-publish feedback loop.

## Current state

- Phase 1: complete
- Data Model V2: complete and merged
- Next: GSC/GA4 provider clients → source registry → LangGraph interrupt/resume

## Relevant context

- `.platform/STATUS.md`
- `.platform/architecture.md`
- `.platform/domains/data-architecture.md`
- `docs/seo-platform-gap-analysis-roadmap.md`

**Never load:** `work/archive/*`
