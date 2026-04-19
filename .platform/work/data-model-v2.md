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
- **What just happened:** (auto) a72fee6: Fix audit findings: consolidate migration, add provenance + freshness tests (48 pass)
- **Current focus:** —
- **Next action:** (auto-saved from commit — update next action manually)
- **Blockers:** none

## Progress log
_Append-only. `agentboard checkpoint` prepends a dated line and auto-trims to the last 10 entries. Format: `2026-04-19 HH:MM — <what happened>`._

2026-04-19 12:52 — (auto) a72fee6: Fix audit findings: consolidate migration, add provenance + freshness tests (48 pass)

2026-04-19 12:40 — (auto) 0478aa5: chore: absorb agentboard hook auto-updates

2026-04-19 12:40 — (auto) 949a5bb: chore: absorb agentboard hook auto-updates

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

## 🔍 Audit — 2026-04-19

> Run via Stream / Feature Analysis Protocol — 1 parallel agent (sonnet).

### ⚡ Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🟢 |
| **Tests** | 🟡 |
| **Security** | 🟢 |
| **Code Quality** | 🟢 |

> All done criteria met, no stubs. Test gap on provenance + freshness field persistence.

### ✅ Implementation — all done criteria verified

| Component | Status | Location |
|---|:---:|---|
| Keyword lifecycle/locale/freshness/provenance | ✅ | `models/keyword.py:36-46` |
| OpportunityScoreRecord with formula_version | ✅ | `models/keyword.py:90-108` |
| ContentBriefRecord provenance (run_id, agent_version, model_id) | ✅ | `models/content.py:40-42` |
| SerpResult provenance (run_id, agent_version, model_id) | ✅ | `models/serp.py:41-43` |
| SearchConsoleRecord (GSC) | ✅ | `models/tracking.py:27-42` |
| AnalyticsRecord (GA4) | ✅ | `models/tracking.py:44-56` |
| Additive SQLite migration | ✅ | `db/migrations.py:6-88` |
| estimate_difficulty() from SERP features | ✅ | `utils/serp_signals.py:30-65` |
| avg_interest volume proxy | ✅ | `utils/serp_signals.py:68-75` |
| SerpAgent writes difficulty_estimate to keyword | ✅ | `agents/serp_agent.py:65-68` |
| SynthesisAgent uses both new signals | ✅ | `agents/synthesis_agent.py:52-78` |
| All models registered in engine.py | ✅ | `db/engine.py:25-40` |
| Repo methods for new monitoring tables | ✅ | `db/crud.py:279-318` |

### 🧪 Test gaps

| Area | Status |
|---|:---:|
| Provenance round-trip (run_id persists to DB) | 🔴 None |
| Freshness fields persist after agent runs | 🔴 None |
| SerpResult schema_version="v2" persisted | 🟡 Thin |

### 🔧 Issues

| Pri | Issue | Location |
|---|---|---|
| 🟡 | No test verifies run_id/agent_version/model_id DB round-trip | `serp_agent.py:60-62` |
| 🟡 | No test verifies serp_fresh_at / trend_fresh_at written by agents | `serp_agent.py:66`, `trend_agent.py:45` |
| 🟡 | ContentBriefRecord columns in migrations twice (harmless, confusing) | `db/migrations.py:29-61` |
| ⚪ | crud.py is 342 lines (over 300 soft limit) | `db/crud.py` |
| ⚪ | GSC/GA4 provider clients not yet implemented | next stream |

### 🎯 Close checklist

```
✅ All done criteria verified
✅ Add provenance round-trip test (run_id persists)
✅ Add freshness field persistence test
✅ Consolidate ContentBriefRecord migration block
□  Human sign-off → closure_approved: true → archive
```
