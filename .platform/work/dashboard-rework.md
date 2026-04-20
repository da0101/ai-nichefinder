---
stream_id: stream-dashboard-rework
slug: dashboard-rework
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [viewer]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/dashboard-rework
created_at: 2026-04-20
updated_at: 2026-04-20
closure_approved: false
---

# dashboard-rework

## Scope

- Replace the inline HTML/JS viewer with a React 18 + shadcn/ui + Tailwind app at `apps/dashboard/`
- Add live polling (30s interval) so DB updates are visible without restarting the server
- Python server serves built `dist/` static files; all existing `/api/` routes unchanged
- Built `dist/` committed to git so `seo view` works without a node build step
- **Out of scope:** any control/action features (approve briefs, trigger workflows) — those are Phase 2

## Done criteria

- [x] `apps/dashboard/` scaffolded with Vite + React 18 + TypeScript + Tailwind + shadcn/ui
- [x] Dashboard loads all existing data (stats bar, keyword list, keyword detail, brief, SERP pages)
- [x] Live polling: stats + sidebar refresh every 30s without page reload
- [x] `viewer_server.py` serves `dist/` static files; falls back to inline HTML if dist not built
- [x] `npm run build` produces `dist/` which works when served by the Python server
- [x] All shadcn/ui pre-delivery checklist items pass (contrast, cursors, icons, hover states)
- [x] `.platform/domains/viewer.md` updated to reflect new architecture
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated with React/shadcn/ui decision
- [ ] Manual verification: `seo view` opens browser, live refresh works, all sections render

## Key decisions

_Append-only. Format: `YYYY-MM-DD — <decision> — <rationale>`_

2026-04-20 — React + Vite + shadcn/ui for dashboard — Vanilla HTML/JS embedded in Python is hard to evolve; React enables live polling, future control features, and responsive layout. User explicitly requested React + shadcn/ui. npm/Node.js toolchain accepted by owner.
2026-04-20 — Built dist/ committed to git — So `seo view` works without requiring `npm install` first. Keeps the CLI local-first, no build step on end-user side.
2026-04-20 — Python server serves dist/ files — No separate web server or proxy; keeps the single-command `seo view` UX intact.

## Resume state

- **Last updated:** 2026-04-20 by claude-code
- **What just happened:** Full implementation complete — React app built, viewer_server.py updated, domain file updated
- **Current focus:** Stage 6 — awaiting human verification + commit approval
- **Next action:** User runs `seo view`, verifies live refresh and all sections load correctly, then approves commit
- **Blockers:** none

## Progress log

2026-04-20 — Implementation complete. React app (22 files, builds to dist/), viewer_server.py serves dist/ with inline HTML fallback, domain file updated, decision #14 recorded.
2026-04-20 11:00 — Stream bootstrapped. Design system generated (data-dense dashboard, blue/amber, Fira Code/Fira Sans). Plan proposed inline.

## Open questions

_None_

---

## 🔍 Audit Report

_Status: not yet run_
