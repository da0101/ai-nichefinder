---
domain_id: dom-repo-topology
slug: repo-topology
status: active
repo_ids: [repo-primary]
related_domain_slugs: [rest-api-control-plane, viewer]
created_at: 2026-04-24
updated_at: 2026-04-24
---

# repo-topology

## What this domain does

Defines the top-level directory layout and package boundaries so the project can evolve cleanly and, if needed, split into separate frontend and backend repositories later without a second large reorg.

It covers where frontend code lives, where backend code lives, which build/runtime files stay shared at the repo root, and which paths are considered stable import/build contracts.

## Backend / source of truth

- Python workspace members currently live under `backend/apps/cli`, `backend/packages/core`, and `backend/packages/db`.
- Root `pyproject.toml` defines the `uv` workspace membership and is the current backend package graph entrypoint.
- Backend runtime and API/server code currently live in `backend/apps/cli/src/nichefinder_cli/`.
- Stable backend invariants: CLI scripts keep working, workspace imports keep resolving, and tests/build commands remain discoverable from the repo root.

## Frontend / clients

- React dashboard currently lives in `frontend/dashboard/`.
- Built frontend assets are still served by the backend viewer/API layer.
- Stable frontend invariants: dashboard build still works, API route assumptions stay unchanged, and the future frontend repo boundary is obvious from the directory tree.

## API contract locked

- Frontend must continue talking only to typed `/api/*` routes, not shell commands or direct filesystem paths.
- Backend package/import paths may be adapted during reorg, but runtime behavior and REST contract shapes should remain stable through compatibility updates.
- Repo-topology changes must not silently change how `uv run pytest -q`, `npm run build`, or `seo view` are invoked without explicit docs and wrapper updates.

## Key files

- `pyproject.toml`
- `backend/apps/cli/pyproject.toml`
- `frontend/dashboard/`
- `backend/packages/core/`
- `backend/packages/db/`
- `.platform/architecture.md`
- `.platform/work/rest-api-control-plane.md`

## Decisions locked

- The frontend/backend split should be explicit at the top level, not implied by mixed `apps/` and `packages/` naming.
- The stable Phase 1 backend boundary is `backend/{apps,packages}`, not a forced flattening that would rename Python ownership boundaries without product value.
- Business logic should not move just to satisfy folder naming; the goal is clearer topology, not churn for its own sake.
- Shared root config should stay minimal and intentional so future repo extraction is mechanical.
- Any reorg must preserve existing CLI, test, and build entrypoints through compatibility updates during the transition.
