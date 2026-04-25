---
domain_id: dom-rank-tracking
slug: rank-tracking
status: active
repo_ids: [repo-primary]
related_domain_slugs: [keyword-research, content-production]
created_at: 2026-04-17
updated_at: 2026-04-19
---

# rank-tracking

## What this domain does

Measures whether published articles are actually improving search visibility and keeps API usage visible enough to avoid accidental overspend. This is the feedback loop that tells the operator whether the earlier research and content decisions are paying off.

## Backend / source of truth

- `RankingSnapshot`, `PerformanceRecord`, and `ApiUsageRecord` hold post-publication evidence and budget tracking.
- `check_rankings` resolves published URLs against current SERP positions and persists snapshots.
- Repository helpers expose ranking history, top opportunities, content counts, and monthly API usage.

## Frontend / clients

- `nichefinder rank check` and `rank sync` record current positions for published content.
- `nichefinder report` summarizes top opportunities, article counts, and content-type performance.
- `nichefinder budget` shows current monthly provider usage across SerpAPI and Gemini.
- `nichefinder view` shows ranking, article, and usage summaries in a local read-only browser surface.

## API contract locked

- Rank checks only inspect articles already marked as published.
- Budget reporting must reflect tracked usage records rather than ad hoc estimates.
- New measurement providers must fit the same local-first persistence model.

## Key files

- `backend/apps/cli/src/nichefinder_cli/commands/ranks.py`
- `backend/apps/cli/src/nichefinder_cli/main.py`
- `backend/apps/cli/src/nichefinder_cli/workflows.py`
- `backend/core/src/nichefinder_core/models/tracking.py`
- `backend/core/src/nichefinder_core/sources/serpapi.py`
- `backend/db/src/nichefinder_db/crud.py`

## Decisions locked

- Ranking evidence matters because content that does not earn visibility is not success.
- Usage and spend need to stay inspectable from the CLI.
- Post-publication feedback remains local and manual until the operator needs more automation.
