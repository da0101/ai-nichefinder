---
stream_id: stream-rest-api-control-plane
slug: rest-api-control-plane
type: feature
status: in-progress
agent_owner: codex
domain_slugs: [rest-api-control-plane]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/rest-api-control-plane
created_at: 2026-04-24
updated_at: 2026-04-24
closure_approved: false
---

# rest-api-control-plane

## Scope

- Define a typed REST API surface for existing local app actions instead of treating shell commands as the integration layer.
- Keep the first slice local-first and compatible with the current viewer server and React dashboard.
- Add a foundation for async job/task execution so long-running workflows can later be called through REST without blocking HTTP requests.
- Make the API cloud-ready in shape: explicit actions, request validation, profile isolation, and no arbitrary command execution.
- Out of scope for the first slice: full cloud deployment, multi-user auth, public internet exposure, or replacing the CLI.

## Done criteria

- [x] Architecture plan for REST control plane is approved or accepted as the working design.
- [x] Existing dashboard/profile endpoints are organized into a documented typed API surface.
- [x] A minimal job/task API exists for at least one long-running workflow or a safe stub with durable status semantics.
- [x] Mutating endpoints have a local/cloud safety story documented and at least local guardrails tested.
- [x] Tests cover happy path and failure path for the new API/job layer.
- [x] `uv run pytest` passes.
- [x] `npm run build` passes if dashboard code changes.
- [x] Manual verification: local API calls can drive profile management and one workflow action without shelling out.
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions

2026-04-24 — REST wraps typed application actions, not shell commands — arbitrary shell execution would become remote code execution if the local server is ever deployed to cloud.
2026-04-24 — REST job state persists in SQLite — completed and failed job results must survive local server restarts so browser automation and future cloud workers can inspect task outcomes by id.
2026-04-24 — REST writes use a token-or-loopback guard — default localhost operation stays frictionless, but any configured `VIEWER_API_TOKEN` becomes mandatory for mutating requests and blocks proxy-loopback bypasses.
2026-04-24 — Learning-memory review routes use explicit request/response models — review and approval payloads should share one typed contract across backend, tests, and dashboard code instead of drifting as ad hoc dicts.
2026-04-24 — Keyword cluster reads stay side-effect free — REST cluster inspection should project clusters in memory instead of calling the existing repository method that persists cluster rows as a byproduct.
2026-04-24 — FastAPI is the transport boundary — route handlers stay thin and reuse the typed action/data/job layer so a future cloud deployment does not couple HTTP details to workflow logic.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-24 by codex
- **What just happened:** Replaced the custom viewer HTTP transport with FastAPI + uvicorn, preserved the existing typed action/data/job layer, and kept all current REST endpoints green; full suite passes at 125.
- **Current focus:** —
- **Next action:** Tighten the FastAPI app boundary further, likely by splitting route modules and then exposing the next typed rank/workflow surface.
- **Blockers:** none

## Progress log

2026-04-24 20:34 — Replaced the custom localhost HTTP transport with FastAPI + uvicorn, kept the typed action/data/job layer intact, and verified full suite green at 125 passed.
2026-04-24 20:02 — Added typed keyword list/cluster/detail REST reads, kept keyword cluster reads side-effect free, and verified full suite green at 125 passed.

2026-04-24 18:26 — Added typed noise/training/final review contracts, new noise-review and noise-approve REST endpoints, and fixed default-profile resolution in the review layer; full pytest and dashboard build pass.

2026-04-24 19:12 — Added typed learning-memory review contracts plus `noise-review`/`noise-approve` REST endpoints, fixed default-profile resolution, and verified full suite green at 124 passed.

2026-04-24 18:09 — Added explicit Python API models, matching TypeScript interfaces, and typed rewrite/monitor-sync jobs; full pytest and dashboard build pass.

2026-04-24 17:47 — Added articles/report/budget endpoints, article approve/publish mutations, and settings-aware direct actions; full pytest and dashboard build pass.
2026-04-24 18:28 — Added explicit Python API models, matching TypeScript interfaces, and typed `rewrite`/`monitor-sync` REST jobs; full suite green at 120 passed.

2026-04-24 17:39 — Extended the REST control plane with allowlisted brief and write jobs, persisted job results, and full test/build verification.
2026-04-24 18:02 — Added `articles`, `report`, and `budget` read endpoints plus article `approve`/`publish` mutations with real DB-backed HTTP coverage; full suite green at 118 passed.

2026-04-24 17:22 — Completed the first REST control-plane slice: typed jobs, SQLite-persisted job state, and token-or-loopback guards for mutating endpoints; full pytest and dashboard build pass.
2026-04-24 17:42 — Added allowlisted `brief` and `write` REST jobs with persisted status/results and HTTP coverage; full suite green at 116 passed.

2026-04-24 17:03 — Added SQLite-backed JobRecord persistence for REST jobs, repository CRUD, settings-aware job API wiring, and restart-survival coverage; uv pytest and dashboard build pass.
## Open questions

- Which remaining CLI surface should be exposed next: rank-history reads, keyword mutation workflows, or the remaining workflow jobs?

---

## 🔍 Audit Report

_Status: not yet run_
