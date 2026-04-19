---
stream_id: stream-data-model-v2
slug: data-model-v2
type: feature
status: in-progress
agent_owner: codex-cli
domain_slugs: [data-architecture]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/data-model-v2
created_at: 2026-04-19
updated_at: 2026-04-19
closure_approved: false
---

# data-model-v2

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope
- Design and implement Data Model V2 as the next roadmap dependency after the Phase 1 foundation.
- Add explicit lifecycle, freshness, provenance, locale, and score-versioning support to the persistence layer.
- Introduce the missing first-class entities that later agent families need, without breaking the working Phase 1 CLI flows.
- Update repository methods and migration scaffolding so later provider/monitoring work can build on stable contracts.
- Out of scope: full GSC/GA4 provider integration, full six-agent orchestration runtime, and distribution/technical agent implementation.

## Done criteria
- [ ] A concrete Data Model V2 target schema is defined in code and project docs.
- [ ] The persistence layer supports first-class records or fields for lifecycle, freshness, provenance, locale, and score versioning where the roadmap requires them.
- [ ] Existing Phase 1 CLI flows still run after the schema changes or have an explicit migration-compatible path.
- [ ] Repository methods and tests cover the new/changed persisted entities.
- [ ] Manual verification confirms the migrated local database can still serve the CLI and viewer flows.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
_Append-only. Format: `2026-04-19 — <decision> — <rationale>`_

2026-04-19 — Start Phase 2 platformization with Data Model V2 instead of jumping straight to six-agent orchestration — the roadmap explicitly says orchestration on top of weak contracts is the wrong order.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 by codex-cli
- **What just happened:** Opened the Phase 2 branch and registered the new stream around Data Model V2, following the roadmap’s stated build order.
- **Current focus:** schema and persistence planning
- **Next action:** audit the current models and repository layer against the roadmap’s required entities and decide the smallest safe migration slice.
- **Blockers:** none

## Progress log
_Append-only. `agentboard checkpoint` prepends a dated line and auto-trims to the last 10 entries. Format: `2026-04-19 HH:MM — <what happened>`._

## Open questions
_Things blocked on user input. Remove when resolved._

---

## 🔍 Audit Report

> **Required:** After every audit request, paste the full standardized report here.
> Do NOT leave the audit only in chat — it must be anchored here so the next session has it.
> Format: `.platform/workflow.md` → Stream / Feature Analysis Protocol → Step 4 template.
> After a clean re-audit (all 🟢), remove this section before stream closure.

_Status: not yet run_
