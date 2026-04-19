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
- [x] A concrete Data Model V2 target schema is defined in code and project docs.
- [x] The persistence layer supports first-class records or fields for lifecycle, freshness, provenance, locale, and score versioning where the roadmap requires them.
- [x] Existing Phase 1 CLI flows still run after the schema changes or have an explicit migration-compatible path.
- [x] Repository methods and tests cover the new/changed persisted entities.
- [x] Manual verification confirms the migrated local database can still serve the CLI and viewer flows.
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions
_Append-only. Format: `2026-04-19 — <decision> — <rationale>`_

2026-04-19 — Start Phase 2 platformization with Data Model V2 instead of jumping straight to six-agent orchestration — the roadmap explicitly says orchestration on top of weak contracts is the wrong order.
2026-04-19 — Make the first V2 slice additive instead of a big-bang rewrite — Phase 1 CLI/viewer compatibility is more important than landing every future entity in one migration.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 by danilulmashev (auto)
- **What just happened:** (auto) 8479d09: Update stream file and log after agentboard auto-update
- **Current focus:** —
- **Next action:** (auto-saved from commit — update next action manually)
- **Blockers:** none

## Progress log
_Append-only. `agentboard checkpoint` prepends a dated line and auto-trims to the last 10 entries. Format: `2026-04-19 HH:MM — <what happened>`._

2026-04-19 12:39 — (auto) 8479d09: Update stream file and log after agentboard auto-update

2026-04-19 12:39 — (auto) 0cee149: update

2026-04-19 12:38 — (auto) e8342a1: update

2026-04-19 12:37 — (auto) e1e6613: Data Model V2: scoring signals, monitoring contracts, and provenance

2026-04-19 19:30 — Fixed dead volume + difficulty scoring: pytrends avg_interest used as volume proxy, deterministic difficulty estimator from SERP features/authority domains. 46/46 tests pass.
2026-04-19 18:45 — Second V2 slice: SERP/brief provenance (run_id, agent_version, model_id), SearchConsoleRecord + AnalyticsRecord monitoring tables, PerformanceRecord marked legacy, full schema target doc in data-architecture.md. 29/29 tests pass.
2026-04-19 12:04 — Implemented the first additive Data Model V2 slice: keyword lifecycle/locale/freshness/provenance fields, persisted OpportunityScoreRecord history, repository support, and additive SQLite migration handling; updated stream/domain/memory docs.

- 2026-04-19 18:10 — Added additive V2 schema fields for keyword lifecycle/locale/freshness/provenance, persisted opportunity score history, added SQLite upgrade support, and passed the full test suite
- 2026-04-19 18:20 — Verified the additive migration through the real CLI path with `seo db init` and `seo status`, then removed the transient local DB file to keep the tree clean

## Open questions
_Things blocked on user input. Remove when resolved._

---

## 🔍 Audit Report

> **Required:** After every audit request, paste the full standardized report here.
> Do NOT leave the audit only in chat — it must be anchored here so the next session has it.
> Format: `.platform/workflow.md` → Stream / Feature Analysis Protocol → Step 4 template.
> After a clean re-audit (all 🟢), remove this section before stream closure.

_Status: not yet run_
