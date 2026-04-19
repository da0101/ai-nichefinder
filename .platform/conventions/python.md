# Python Conventions

Last updated: 2026-04-17

## Stack shape

- Python 3.12 workspace managed by `uv`
- Package split:
- `apps/cli` for Typer command surface
- `packages/core` for models, agents, adapters, settings, and orchestration
- `packages/db` for persistence and session/bootstrap helpers

## Rules for this repo

- Keep commands thin. Business logic belongs in `packages/core` or `packages/db`, not in Typer handlers.
- Prefer explicit models with Pydantic/SQLModel over loose dicts once data crosses a package boundary.
- Async stays inside agents, workflows, and adapters; CLI commands may use `asyncio.run(...)` as the sync boundary.
- Read and write through `SeoRepository` rather than spreading raw SQLModel queries across the codebase.
- Respect the repo-wide ceiling of roughly 300 lines per file; split agents, helpers, or parsers before adding complexity.
- Use Ruff defaults already configured in `pyproject.toml` rather than inventing per-file style exceptions.

## Navigation

- Entry point: `apps/cli/src/nichefinder_cli/main.py`
- Runtime wiring: `apps/cli/src/nichefinder_cli/runtime.py`
- Workflow orchestration: `apps/cli/src/nichefinder_cli/workflows.py`
- Domain models: `packages/core/src/nichefinder_core/models/`
- External adapters: `packages/core/src/nichefinder_core/sources/`
- Persistence: `packages/db/src/nichefinder_db/`

## Things to avoid

- Putting provider-specific response parsing in CLI commands
- Hiding paid-vs-free source decisions inside random helper code
- Writing features that bypass settings, repository, or rate-limiter abstractions
