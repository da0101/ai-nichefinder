---
stream_id: stream-repo-cleanup
slug: repo-cleanup
type: chore
status: awaiting-verification
agent_owner: codex-cli
domain_slugs: [repo-hygiene]
repo_ids: [repo-primary]
base_branch: develop
git_branch: chore/repo-cleanup
created_at: 2026-04-19
updated_at: 2026-04-19
closure_approved: false
---

# repo-cleanup

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope
- Remove clearly stale tracked files and duplicate templates that no longer match the actual local-first CLI workflow
- Delete untracked local junk, caches, generated outputs, and runtime state that should not live in the working tree
- Normalize `.platform` bookkeeping so the cleanup stream is the active source of truth during this pass
- Keep active Phase 2 roadmap materials and implementation code intact; this is hygiene, not a product reset
- Out of scope: Data Model V2 implementation, provider integrations, or new runtime architecture work

## Done criteria
- [x] Stale tracked files and duplicate env templates are removed or consolidated with no broken references
- [x] Untracked local junk and generated artifacts identified in the audit are removed from the working tree
- [x] `git status --short` shows only intentional cleanup changes
- [x] Targeted verification passes via repo search and file inventory review
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions
_Append-only. Format: `2026-04-19 — <decision> — <rationale>`_

- 2026-04-19 — Keep a single canonical env template at the repo root — duplicate templates had already drifted and were creating setup ambiguity
- 2026-04-19 — Remove dead docker-compose scaffolding — the project is CLI-first, SQLite-backed, and does not use local container orchestration today

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 — by codex-cli
- **What just happened:** Removed stale tracked docs/tooling, deleted local junk artifacts, and aligned setup docs with the actual codebase
- **Current focus:** Await user verification before archiving the cleanup stream
- **Next action:** If approved, archive `repo-cleanup` and return focus to `data-model-v2`
- **Blockers:** none

## Progress log
_Append-only. `agentboard checkpoint` prepends a dated line and auto-trims to the last 10 entries. Format: `2026-04-19 HH:MM — <what happened>`._

- 2026-04-19 16:30 — Audited tracked/untracked files, identified duplicate env templates, stale architecture/docs artifacts, dead docker scaffolding, and local junk to remove
- 2026-04-19 16:55 — Removed stale docs/tooling, deleted ignored runtime and generated artifacts, and verified there are no remaining references to the removed surfaces

## Open questions
_Things blocked on user input. Remove when resolved._

---

## 🔍 Audit Report

> **Required:** After every audit request, paste the full standardized report here.
> Do NOT leave the audit only in chat — it must be anchored here so the next session has it.
> Format: `.platform/workflow.md` → Stream / Feature Analysis Protocol → Step 4 template.
> After a clean re-audit (all 🟢), remove this section before stream closure.

_Status: not yet run_
