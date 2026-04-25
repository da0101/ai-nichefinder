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
2026-04-24 — Phase 1 layout target is `frontend/dashboard` plus `backend/{apps,core,db}` — this keeps the future repo boundary obvious without implying that internal backend modules are plugins or external libraries.
2026-04-24 — Group root CLI concerns under `backend/apps/cli/src/nichefinder_cli/commands/root/` and reduce `main.py` to Typer app assembly — the root command surface is still part of the backend product boundary, but the implementation should be organized by concern instead of living in one file.
2026-04-24 — Group the remaining CLI implementation under concern folders (`commands/content`, `commands/discovery`, `commands/monitoring`, `commands/system`) and leave the old flat files as compatibility shims — ownership should follow concern folders first, while compatibility imports can stay stable during the transition.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-24 by danilulmashev
- **What just happened:** Grouped the remaining CLI implementation under concern folders with compatibility shims, updated test seams, and re-verified backend/frontend suites.
- **Current focus:** —
- **Next action:** Split App.tsx further into feature-owned sections and keep reducing mixed entry files.
- **Blockers:** none

## Progress log

2026-04-24 22:19 — Grouped the remaining CLI implementation under concern folders with compatibility shims, updated test seams, and re-verified backend/frontend suites.

2026-04-24 22:19 — Grouped the remaining CLI implementation under `commands/{content,discovery,monitoring,system}`, left the old flat command files as compatibility shims, updated test monkeypatch seams, and re-verified `uv run pytest -q`, `npm run test:run`, and `npm run build`.

2026-04-24 21:33 — Grouped the root CLI surface under commands/root and reduced main.py to Typer assembly; updated CLI test patch seams and re-verified backend/frontend suites.

2026-04-24 21:34 — Split the root CLI surface out of `main.py` into grouped `commands/root/{research,reviews,profiles,content,reporting,shared}.py` modules, reduced `main.py` to app assembly, retargeted CLI tests to the new seams, and verified `uv run pytest -q`, `npm run test:run`, and `npm run build`.

2026-04-24 21:16 — Split viewer_actions.py into dedicated service modules for profile, article, workflow, and runtime context; routes and jobs now call those services directly and the suite stayed green.

2026-04-24 21:16 — Split `viewer_actions.py` into dedicated `services/{profile,article,workflow,runtime_context}.py` modules, reduced `viewer_actions.py` to a thin compatibility layer, pointed routes/jobs at the new services directly, and verified `uv run pytest -q`, `npm run test:run`, and `npm run build`.

2026-04-24 21:10 — Renamed backend ownership folders to backend/{core,db} and split the FastAPI transport into dedicated route, response, security, and static-serving modules while keeping pytest and frontend checks green.

2026-04-24 21:10 — Renamed `backend/packages/{core,db}` to `backend/{core,db}` and split `viewer_server.py` into dedicated API route, security, response, and static-serving modules; verified `uv run pytest -q`, `npm run test:run`, and `npm run build`.

2026-04-24 21:06 — Renamed `backend/packages/{core,db}` to `backend/{core,db}`, updated workspace/config/docs references, and re-verified `uv sync`, `uv run pytest -q`, `npm run test:run`, and `npm run build`.

2026-04-24 20:56 — Completed frontend Phase 2A: added a shared typed HTTP client, moved dashboard hooks under feature-owned folders, deleted the generic hooks layer, and introduced Vitest hook/API tests.

## Open questions

- After the naming cleanup to `backend/{apps,core,db}`, should the next backend pass stop at route/service extraction, or is there still a real need to collapse `backend/apps/cli` further?

---

## 🔍 Audit Report

_Status: Phase 1 completed and verified locally; stream remains open for any follow-on cleanup phase._
