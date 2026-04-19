---
domain_id: dom-repo-hygiene
slug: repo-hygiene
status: active
repo_ids: [repo-primary]
related_domain_slugs: []
created_at: 2026-04-19
updated_at: 2026-04-19
---

# repo-hygiene

_Metadata rules: `domain_id` must be `dom-<slug>`, `slug` must match the filename, `repo_ids` should name the repos this domain touches, and `updated_at` should change whenever contracts or touch-points change._

## What this domain does

This domain keeps the repository lean, readable, and accurate so operators are not navigating stale docs, duplicate config, abandoned tooling, or local junk. Its job is to preserve a local-first CLI codebase where the tracked files reflect the actual product surface and active workflow.

## Backend / source of truth

- `.platform/` stream state and memory files define what work is actually active
- Root project config files (`pyproject.toml`, `.env.example`, `README.md`, `AGENTS.md`) are the source of truth for developer workflow
- Tracked repo files should correspond to live code paths, active docs, or deliberate fixtures; local caches, runtime state, and generated artifacts stay untracked

## Frontend / clients

- No dedicated product UI surface
- Touch-points are the repo root, CLI onboarding docs, and the lightweight local viewer already implemented in Phase 1

## API contract locked

- The canonical env template lives at the repo root in `.env.example`
- `.platform/architecture.md` is the active architecture reference; stale duplicate architecture docs should not coexist
- Local runtime state, caches, DB files, and generated outputs must remain ignored unless explicitly promoted to fixtures

## Key files

- `.platform/work/ACTIVE.md`
- `.platform/work/BRIEF.md`
- `.platform/architecture.md`
- `.env.example`
- `README.md`
- `.gitignore`

## Decisions locked

- Keep the repo CLI-first and local-first; do not preserve infra scaffolding that no longer serves a live workflow
- Prefer one canonical file per concern instead of mirrored templates that drift
- Generated local state belongs in ignored paths, not as tracked documentation substitutes
- Cleanup work must not delete roadmap context or active implementation code just because it is unfinished
