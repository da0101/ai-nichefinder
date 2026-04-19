# CLI Conventions

Last updated: 2026-04-17

## Purpose

The CLI is the product. Every command should help the operator decide what to write, what to review, or what to measure next.

## Rules

- Commands expose workflows and summaries, not raw provider dumps.
- Rich tables are preferred for inventory/report views; structured object dumps are acceptable for deeper workflow output.
- Human checkpoints must stay obvious. If a workflow changes publication state or approves content, the command should make that explicit.
- `get_runtime()` is the standard bootstrap path for settings, site config, and DB session context.
- New commands should fit the existing group layout before adding more top-level command names.

## Existing command groups

- `status`, `config`, `budget`, `report`
- `db`
- `keywords`
- `articles`
- `rank`
- top-level workflow commands like `research`, `brief`, `write`, `rewrite`, `publish`

## Things to avoid

- Burying important operator decisions in background automation
- Adding commands that require hosted infrastructure or a daemon without a deliberate architecture change
- Auto-publishing or auto-approving generated content
