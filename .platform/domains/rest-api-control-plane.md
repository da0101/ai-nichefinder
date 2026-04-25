---
title: REST API Control Plane
domain_slug: rest-api-control-plane
last_updated: 2026-04-24
---

# Domain: REST API Control Plane

Expose ai-nichefinder workflows through typed local REST endpoints so the browser UI, local automation, and a future cloud deployment can call the same application actions without shelling out to arbitrary commands.

## Scope

| Layer | Files / Modules | Responsibility |
|---|---|---|
| HTTP server | `backend/apps/cli/src/nichefinder_cli/viewer_server.py`, `viewer_html.py` | FastAPI app that serves dashboard assets and `/api/*` routes, with a minimal HTML fallback when the built dashboard is missing |
| API action layer | `backend/apps/cli/src/nichefinder_cli/viewer_actions.py`, `viewer_profile_data.py`, `viewer_data.py` | Thin request/response wrappers around runtime/domain services |
| Runtime/services | `backend/apps/cli/src/nichefinder_cli/runtime.py`, `workflows.py` | Builds settings, repositories, agents, and executes workflows |
| Core workflows | `backend/packages/core/src/nichefinder_core/**` | Domain models, agents, source clients, scoring, validation, generation |
| Persistence | `backend/packages/db/src/nichefinder_db/**` | SQLite-backed records used by CLI and API |
| Frontend | `frontend/dashboard/` | React client that should consume only `/api/*`, not shell commands |

## Invariants

- REST endpoints must call typed Python functions, not arbitrary shell commands.
- Long-running workflows must be represented as jobs/tasks instead of blocking request handlers indefinitely.
- Local-first behavior remains the default: loopback binding, SQLite, filesystem outputs, and `.env` settings.
- Mutating REST endpoints must allow writes only from loopback by default, or require a configured bearer token when `VIEWER_API_TOKEN` is set.
- Cloud-readiness requires explicit auth, request validation, tenant/profile isolation, and no raw command execution endpoint.
- Cost-incurring actions must remain explicit and usage-accounted.
- FastAPI is the transport boundary; workflow and repository logic stays in typed action/data/job helpers, not in route handlers.

## API Surface Direction

Phase 1 wraps existing safe actions:
- profile list/create/update/delete/switch
- dashboard/status reads
- profile config reads/writes
- noise/training/final review reads and approvals
- free validation

Phase 2 adds async jobs for long-running workflows:
- research jobs
- brief/content generation jobs
- monitor sync and rank-check jobs
- future agent task dispatch jobs

## Known Risks

- `viewer_server.py` still carries a broad route surface and should be split further if the REST API keeps growing.
- Current write guard is a shared static bearer token or loopback-only policy, not a multi-user auth system.
- CLI commands are not all factored into reusable service functions yet.
- Exposing "shell functions" directly would become remote code execution in a cloud deployment.
