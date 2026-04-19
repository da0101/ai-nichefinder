# Deployment Conventions

Last updated: 2026-04-17

## Current reality

There is no hosted deployment pipeline yet. "Release" currently means the local CLI, database, site config, and output directories work correctly on the operator's machine.

## Practical rules

- Prefer reversible local changes and keep the SQLite DB backed up before risky migrations or schema work.
- If a command changes on-disk output formats, note the impact on existing files in the task summary.
- Do not invent staging/prod workflows in docs or code until the project actually needs them.

## Rollback mindset

- Code rollback: git revert or local checkout discipline
- Data rollback: restore SQLite backup or output files if a workflow corrupts local state
- Provider rollback: disable the adapter in settings or stop using the command
