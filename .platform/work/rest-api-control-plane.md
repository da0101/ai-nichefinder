---
stream_id: stream-rest-api-control-plane
slug: rest-api-control-plane
type: feature
status: awaiting-verification
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

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-24 by danilulmashev
- **What just happened:** Completed the first REST control-plane slice: typed jobs, SQLite-persisted job state, and token-or-loopback guards for mutating endpoints; full pytest and dashboard build pass.
- **Current focus:** —
- **Next action:** Get human verification and commit this slice, or extend the API into the next typed workflow/job surface.
- **Blockers:** none

## Progress log

2026-04-24 17:22 — Completed the first REST control-plane slice: typed jobs, SQLite-persisted job state, and token-or-loopback guards for mutating endpoints; full pytest and dashboard build pass.

2026-04-24 17:03 — Added SQLite-backed JobRecord persistence for REST jobs, repository CRUD, settings-aware job API wiring, and restart-survival coverage; uv pytest and dashboard build pass.
2026-04-24 17:21 — Added write guards for mutating REST endpoints: loopback-only by default, mandatory bearer token when `VIEWER_API_TOKEN` is configured; documented the policy and added denial-path tests.

2026-04-24 — Stream registered; domain file created; ACTIVE.md and BRIEF.md updated.
2026-04-24 — Added the first typed REST job API slice: local status, job listing/detail, allowlisted `validate-free` jobs, shell-action rejection, tests, and decision #21.
2026-04-24 — Added allowlisted `research` jobs that call `run_full_pipeline()` through a JSON-safe action wrapper instead of shelling out; full suite green at 110 passed.
2026-04-24 — Persisted REST job rows in SQLite via `JobRecord` and repository CRUD; added restart-survival API test; full suite green at 111 passed.

## Open questions

- Should the next stream extend this control plane into more typed workflow jobs, or stop here and close the first slice?

---

## 🔍 Audit Report

_Status: not yet run_
