---
domain: viewer
title: Local Web Viewer
status: active
last_updated: 2026-04-19
---

# viewer — Local Web Viewer

The local web viewer (`seo viewer`) is a FastAPI/HTTP server that serves an in-browser UI for exploring pipeline results stored in SQLite. It is the only non-CLI surface in the project.

## Cross-layer touch-points

| Layer | Path | Role |
|---|---|---|
| CLI command | `apps/cli/src/nichefinder_cli/commands/viewer.py` | `seo viewer` entrypoint, launches server |
| Data layer | `apps/cli/src/nichefinder_cli/viewer_data.py` | Reads from SQLite via `SeoRepository`, returns JSON |
| Server/HTML | `apps/cli/src/nichefinder_cli/viewer_server.py` | Inline FastAPI app + HTML/JS template |
| Repository | `packages/db/src/nichefinder_db/crud.py` | `SeoRepository` methods consumed by viewer_data |
| Models | `packages/db/src/nichefinder_db/models.py` | ORM tables; viewer reads `OpportunityScoreRecord`, `Keyword`, `Article` |

## Invariants

1. The viewer is **read-only** — it must never write to the DB.
2. It starts on `localhost:8080` by default; port is configurable.
3. All data is served from local SQLite — no external API calls from the viewer.
4. The HTML/JS is inlined in `viewer_server.py` — no build step, no node_modules.

## Score sub-components

`OpportunityScoreRecord` stores 5 sub-scores: `volume_score`, `difficulty_score`, `trend_score`, `intent_score`, `competition_score`. These must be exposed by `viewer_data.py` for the UI to display score breakdowns.

## UX goals

- Non-SEO users must understand what they're seeing (plain-English labels)
- Color-coded score bars (green ≥70, yellow ≥50, red <50)
- Score breakdown per keyword visible at a glance
- Priority/action visible without needing to know SEO jargon
