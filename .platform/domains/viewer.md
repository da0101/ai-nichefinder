---
domain: viewer
title: Local Web Viewer
status: active
last_updated: 2026-04-20
---

# viewer — Local Web Viewer

The local web viewer (`seo view`) is a Python HTTP server that serves a React + shadcn/ui dashboard for exploring pipeline results stored in SQLite and running limited profile-testing actions from the browser. It is the only non-CLI surface in the project.

## Cross-layer touch-points

| Layer | Path | Role |
|---|---|---|
| CLI command | `backend/apps/cli/src/nichefinder_cli/commands/viewer.py` | `seo view` entrypoint, launches server |
| Data layer | `backend/apps/cli/src/nichefinder_cli/viewer_data.py` | Reads from SQLite via `SeoRepository`, returns JSON |
| Server | `backend/apps/cli/src/nichefinder_cli/viewer_server.py` | HTTP server — serves React dist/ + JSON API |
| React app | `frontend/dashboard/` | Vite + React 18 + TypeScript + Tailwind + shadcn/ui |
| Built assets | `frontend/dashboard/dist/` | Pre-built, committed — served by Python server |
| Repository | `backend/db/src/nichefinder_db/crud.py` | `SeoRepository` methods consumed by viewer_data |
| Models | `backend/db/src/nichefinder_db/models.py` | ORM tables; viewer reads `OpportunityScoreRecord`, `Keyword`, `Article` |

## Invariants

1. The viewer is local-only and may perform only low-risk testing actions: switching profiles, creating profiles, saving profile config, approving training signals, and triggering `validate-free`.
2. It starts on `localhost:8765` by default; port is configurable.
3. All data is served from local SQLite — no external API calls from the viewer.
4. `frontend/dashboard/dist/` is committed to git so `seo view` works without running `npm install`.
5. If `dist/index.html` is missing, the server falls back to the legacy inline HTML — `seo view` never hard-fails.
6. All `/api/` routes are handled by Python; the React app calls them via `fetch('/api/...')`.

## API endpoints (served by Python)

| Route | Handler | Response |
|---|---|---|
| `GET /` | `viewer_server.py` | Serves `dist/index.html` (or inline HTML fallback) |
| `GET /assets/*` | `viewer_server.py` | Serves static assets from `dist/assets/` |
| `GET /api/dashboard` | `viewer_data.load_dashboard()` | JSON: summary + keywords + articles + usage |
| `GET /api/keywords/:id` | `viewer_data.load_keyword_detail()` | JSON: full keyword analysis |
| `GET /api/profiles` | `viewer_profile_data.load_profiles()` | JSON: active profile + profile summaries |
| `POST /api/profiles/active` | `viewer_profile_data.switch_active_profile()` | JSON: updated active profile summary |
| `POST /api/profiles` | `viewer_actions.create_profile_action()` | JSON: created profile metadata |
| `GET /api/profile-config` | `viewer_actions.load_profile_config()` | JSON: editable site config for a profile |
| `POST /api/profile-config` | `viewer_actions.save_profile_config_action()` | JSON: saved site config |
| `GET /api/training-review` | `viewer_profile_data.load_training_review()` | JSON: training candidates + approved signals |
| `POST /api/training-approve` | `viewer_profile_data.approve_training_review()` | JSON: updated training review payload |
| `GET /api/final-review` | `viewer_profile_data.load_final_review()` | JSON: cross-profile summary |
| `POST /api/validate-free` | `viewer_actions.run_validate_free_action()` | JSON: structured validation result bundle |

## React app structure (`frontend/dashboard/src/`)

| File | Role |
|---|---|
| `App.tsx` | Layout shell — header, stats bar, sidebar, detail pane |
| `components/ProfileSwitcher.tsx` | Active profile selector and profile summary cards |
| `components/ProfileConfigPanel.tsx` | In-browser profile creation + editable business context |
| `components/TrainingReviewPanel.tsx` | Training candidate review + approval actions |
| `components/ValidationLabPanel.tsx` | Trigger `validate-free` and inspect result bundles |
| `components/FinalReviewPanel.tsx` | Cross-profile comparison summary |
| `hooks/useDashboard.ts` | Polls `/api/dashboard` every 30s |
| `hooks/useKeywordDetail.ts` | Fetches `/api/keywords/:id` with AbortController |
| `hooks/useProfiles.ts` | Loads/switches/creates profiles |
| `hooks/useProfileConfig.ts` | Loads and saves profile config |
| `hooks/useTrainingReview.ts` | Polls training candidates and posts approvals |
| `hooks/useValidateFreeAction.ts` | Triggers `validate-free` from the browser |
| `hooks/useFinalReview.ts` | Polls cross-profile review summary |
| `components/KeywordList.tsx` | Sidebar — scrollable list with search filter |
| `components/KeywordDetail.tsx` | Right panel — score, breakdown, brief, SERP |
| `components/ScoreBreakdown.tsx` | 5-factor weighted score bars |
| `components/StatsBar.tsx` | KPI strip (4 stats) |
| `components/LiveIndicator.tsx` | "Updated X ago" + manual refresh button |

## Dev loop

- **Prod (`seo view`):** Python serves `dist/`. Rebuild with `cd frontend/dashboard && npm run build` when frontend changes.
- **Dev (frontend):** `cd frontend/dashboard && npm run dev` — Vite on :5173 proxies `/api/` to :8765. Run Python server separately.

## Score sub-components

`OpportunityScoreRecord` stores 5 sub-scores: `volume_score`, `difficulty_score`, `trend_score`, `intent_score`, `competition_score`. Exposed by `viewer_data.py` and rendered in `ScoreBreakdown.tsx`.

## UX goals

- Non-SEO users must understand what they're seeing (plain-English labels)
- Color-coded score bars (green ≥70, amber ≥50, red <50)
- Live refresh — DB updates visible within 30s without server restart
- Score breakdown per keyword visible at a glance
- Priority/action visible without needing to know SEO jargon
- The browser workflow should reduce CLI dependence for profile setup and testing, but it must not become a full publish/admin surface
