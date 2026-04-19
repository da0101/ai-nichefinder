# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Feature:** _Data Model V2_
**Status:** in-progress
**Stream file:** `work/data-model-v2.md`

---

## What we're building

We are starting the next roadmap phase by upgrading the persistence and contract layer into Data Model V2. This is the substrate required before adding real first-party monitoring, broader provider clients, and the eventual six-agent orchestration runtime.

## Why

The roadmap is explicit: do not jump straight into “6-agent autonomous orchestration.” First fix the schema and provider contracts, otherwise every later agent family will sit on lossy blobs and force a breaking rewrite.

## What done looks like

- The persistence layer can represent lifecycle, freshness, provenance, locale, and score versioning explicitly.
- Missing roadmap entities are either added or intentionally staged with a documented migration plan.
- Existing Phase 1 flows still work after the migration.
- The repo is ready for GSC/GA4/provider work without another schema rethink.

## Current state

Phase 1 is complete. The next roadmap-correct step is Data Model V2, followed by source registry/provider clients, then real monitoring and only later deeper orchestration.

## Relevant context

- `.platform/STATUS.md`
- `.platform/architecture.md`
- `.platform/domains/data-architecture.md`
- `.platform/domains/keyword-research.md`
- `.platform/domains/content-production.md`
- `.platform/domains/rank-tracking.md`
- `docs/seo-platform-gap-analysis-roadmap.md`

**Never load:** `work/archive/*`
