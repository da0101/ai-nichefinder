---
stream_id: stream-repo-topology-reorg
slug: repo-topology-reorg
type: refactor
status: in-progress
agent_owner: codex
domain_slugs: [repo-topology]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/repo-topology-reorg
created_at: 2026-04-24
updated_at: 2026-04-24
closure_approved: false
---

# repo-topology-reorg

## Scope

- Reorganize the repo so frontend and backend live under clearly separated top-level directories that could later become separate repositories with minimal friction.
- Preserve current CLI behavior, dashboard build behavior, REST/API behavior, and test entrypoints while the layout changes.
- Make shared root files intentional: only keep repo-level orchestration/config that truly belongs at the root.
- Out of scope for the first phase: splitting into two repos right now, changing product behavior, or rewriting the Python package architecture beyond what the directory move requires.

## Done criteria

- [x] A phased reorg plan is agreed and scoped to safe slices.
- [x] Frontend and backend live under explicit top-level directories with updated config paths.
- [x] `uv run pytest -q` passes after the move.
- [x] `npm run build` passes after the move.
- [x] Manual verification: `seo view` still serves the dashboard/API successfully after the layout change.
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions

2026-04-24 — Treat the repo topology change as a phased refactor, not a one-shot move — directory churn across workspace config, tests, and frontend build paths is too broad to do safely without staged checkpoints.
2026-04-24 — Phase 1 layout target is `frontend/dashboard` plus `backend/{apps,packages}` — this keeps the future repo boundary obvious without rewriting the existing Python workspace/package architecture.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-24 by danilulmashev
- **What just happened:** Completed Phase 1 of the repo split: moved the dashboard to frontend/dashboard, moved the Python workspace under backend/, updated path/config references, and re-verified pytest, dashboard build, and seo view.
- **Current focus:** repo topology phase 1 verification
- **Next action:** Decide whether to keep backend/{apps,packages} as the stable long-term boundary or do a smaller root-config cleanup follow-up.
- **Blockers:** none

## Progress log

2026-04-24 20:14 — Completed Phase 1 of the repo split: moved the dashboard to frontend/dashboard, moved the Python workspace under backend/, updated path/config references, and re-verified pytest, dashboard build, and seo view.

2026-04-24 20:16 — Completed Phase 1 of the repo split: `frontend/dashboard` and `backend/{apps,packages}` are live, `uv sync` now resolves the moved workspace, `uv run pytest -q` passed at 125, `npm run build` passed, and `seo view` served both `/` and `/api/dashboard` from the new layout.

2026-04-24 18:47 — Registered the repo-topology reorg stream and domain after the user asked for a mature frontend/backend split; next step is to define the target layout and staged migration plan.

2026-04-24 20:45 — Registered the repo-topology reorg stream and domain; next step is to propose a phased frontend/backend split layout.

## Open questions

- Is there enough future value in flattening `backend/{apps,packages}` into `backend/{cli,core,db}`, or is the current split already the right stable extraction boundary?

---

## 🔍 Audit Report

_Status: Phase 1 completed and verified locally; stream remains open for any follow-on cleanup phase._
