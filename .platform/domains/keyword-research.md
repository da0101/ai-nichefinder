---
domain_id: dom-keyword-research
slug: keyword-research
status: active
repo_ids: [repo-primary]
related_domain_slugs: [content-production, rank-tracking]
created_at: 2026-04-17
updated_at: 2026-04-19
---

# keyword-research

## What this domain does

Finds keyword opportunities worth considering for `danilulmashev.com` and ranks them with enough evidence to decide whether content production should start. It is the front half of the value chain: if this domain is weak, the rest of the system just produces polished noise.

## Backend / source of truth

- `Keyword`, `KeywordCluster`, and `OpportunityScore` are the core entities for discovery and prioritization.
- `KeywordAgent`, `SerpAgent`, `TrendAgent`, and `AdsAgent` contribute the signals used in `run_full_pipeline`.
- `SeoRepository` persists discovered keywords, updates metrics, and clusters related terms.
- Opportunity ranking currently combines volume, difficulty, trend, intent, and competition signals with a deterministic formula.

## Frontend / clients

- `nichefinder research <seed>` runs the end-to-end research flow for a seed keyword.
- `nichefinder research-batch` replays the same flow across configured seed topics.
- `nichefinder keywords list`, `keywords cluster`, and `keywords inspect <keyword-id>` expose the current local keyword inventory and stored evidence to the operator.
- `nichefinder view` provides a lightweight read-only dashboard and keyword detail view over the same stored research artifacts.

## API contract locked

- Commands must return a ranked opportunity view, not raw provider payloads.
- Source-specific parsing stays in adapter/agent layers; Typer commands should not know SerpAPI or Trends response shapes.
- New keyword sources must respect the paid-usage and anti-ban rules in `conventions/data-sources.md`.

## Key files

- `backend/apps/cli/src/nichefinder_cli/main.py`
- `backend/apps/cli/src/nichefinder_cli/workflows.py`
- `backend/apps/cli/src/nichefinder_cli/commands/keywords.py`
- `backend/packages/core/src/nichefinder_core/agents/keyword_agent.py`
- `backend/packages/core/src/nichefinder_core/agents/serp_agent.py`
- `backend/packages/core/src/nichefinder_core/agents/trend_agent.py`
- `backend/packages/core/src/nichefinder_core/agents/ads_agent.py`
- `backend/packages/core/src/nichefinder_core/models/keyword.py`
- `backend/packages/db/src/nichefinder_db/crud.py`

## Decisions locked

- Research quality matters more than keyword volume quantity.
- Paid defaults stay narrow: Gemini is allowed, other sources must remain free or free-tier unless explicitly approved.
- No direct Google scraping belongs in this domain.
- Opportunity scores should remain explainable enough to debug when a keyword is promoted or filtered out.
