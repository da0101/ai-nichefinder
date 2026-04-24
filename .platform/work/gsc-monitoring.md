---
stream_id: stream-gsc-monitoring
slug: gsc-monitoring
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [gsc-monitoring]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/gsc-monitoring
created_at: 2026-04-19
updated_at: 2026-04-21
closure_approved: false
---

# gsc-monitoring

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope

- Implement a Google Search Console API v1 adapter (`gsc_client.py`) that authenticates via OAuth2 and fetches impression/click/CTR/position rows for a configured property.
- Wire the adapter to `SeoRepository.save_search_console_record()` to populate the existing `SearchConsoleRecord` table.
- Expose a `seo monitor sync` CLI command (Typer) that runs the fetch + persist cycle for a configurable date range (default: last 7 days).
- Add settings fields for GSC credentials path and property URL.
- Write integration tests using a mock HTTP layer (no real API calls in CI).
- Out of scope: GA4/AnalyticsRecord, automated scheduling, real-time data, rank-change alerting.

## Done criteria

**GCP prerequisite (human steps before manual verification):**
- Create GCP project, enable Search Console API v1.
- Create service account, download JSON key, add the SA email as a Full User on the GSC property `sc-domain:danilulmashev.com`.
- Set `GSC_CREDENTIALS_PATH=/path/to/key.json` and `GSC_PROPERTY_URL=sc-domain:danilulmashev.com` in `.env`.

- [x] `gsc_client.py` adapter authenticates via service account credentials and fetches `SearchConsoleRecord`-shaped rows from GSC API.
- [x] `seo monitor sync [--days N] [--property URL]` CLI command works end-to-end: fetch → upsert → persist → Rich summary table.
- [x] Re-syncing the same date range updates existing rows (impressions/clicks/ctr/position) rather than inserting duplicates.
- [x] Settings load `GSC_CREDENTIALS_PATH` and `GSC_PROPERTY_URL` from `.env` (never hardcoded).
- [x] At least 5 unit tests cover: API row mapping, empty-result handling, update-on-resync, credentials guard (no path → clear error), CLI upsert path.
- [x] `pytest` full suite still passes (no regressions).
- [ ] Manual verification: after GCP prerequisite steps, `seo monitor sync` runs locally and rows appear in SQLite (blocked on human GCP setup).
- [x] `.platform/memory/log.md` appended.
- [x] `decisions.md` updated if any architectural choices were made.

## Key decisions

_Append-only. Format: `YYYY-MM-DD — <decision> — <rationale>`_

2026-04-19 — GSC-only stream (no GA4) — keeps scope tight; GA4 is a separate client with different auth and data shape.
2026-04-19 — Use `google-api-python-client` + `google-auth-oauthlib` — official Google client, well-maintained, handles token refresh automatically.
2026-04-19 — Update-on-resync (not skip) by composite key (query + page_url + snapshot_date + property_id) — GSC finalizes metrics over a ~2-3 day rolling window; skipping freezes stale numbers from the first sync.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-21 by codex
- **What just happened:** Added direct CLI sync coverage, restored full-suite green at 93 passed, and recorded the Phase 1 duplicate-prevention decision in shared project memory.
- **Current focus:** Await human GCP setup and local end-to-end verification.
- **Next action:** Once credentials are ready, run `seo monitor sync` against the real property and record the result here.
- **Blockers:** none

## Progress log

_Append-only._

2026-04-19 17:44 — (auto) da66d4b: Close viewer-redesign stream: archive, remove from ACTIVE.md

2026-04-19 16:11 — (auto) b049ad1: feat: Rich spinner on every waiting step during seo research

2026-04-19 16:04 — (auto) c217749: fix: pytrends 429 graceful fallback, remove score cap, informational seeds

2026-04-19 15:55 — (auto) 7a80d71: feat: real-time console feedback during seo research pipeline

2026-04-19 13:54 — (auto) 505ff0f: feat: Montreal-focused SEO targeting — location wired end-to-end, seeds updated

2026-04-19 13:42 — (auto) 1abddc4: docs: add CLI cheat sheet

2026-04-19 13:37 — (auto) a9a9c92: feat(db): auto-backup before init, backup/export commands, WAL mode

2026-04-19 13:25 — (auto) 72f6544: feat(gsc-monitoring): GSC adapter, upsert, monitor sync CLI (53 tests pass)

2026-04-19 13:22 — (auto) a396ce1: Register gsc-monitoring stream: domain file, stream file, ACTIVE.md, BRIEF.md

2026-04-19 — Stream registered; domain file created; branch feature/gsc-monitoring created from develop.

2026-04-21 12:10 — Added command-level tests for `seo monitor sync`, restored full-suite green at 93 passed, and recorded the app-level duplicate-prevention decision in shared memory.

## Open questions

_Things blocked on user input. Remove when resolved._

## Audit follow-up — 2026-04-21

- The audit's red blockers are resolved in code: `seo monitor sync` now has direct CLI coverage and `uv run pytest -q` is green at `93 passed`.
- Shared project memory now records the intentional Phase 1 choice to keep GSC duplicate prevention application-level until a real schema-migration need appears.
- The only remaining closure blocker is manual GCP verification on a real property, which is inherently human-operated.

---

## 🔍 Audit — 2026-04-24

> Supersedes previous audit. Run via Stream / Feature Analysis Protocol — 6 parallel/rotated agents.

# 📋 gsc-monitoring — Audit Snapshot

> **Stream:** `gsc-monitoring` · **Date:** 2026-04-24 · **Status:** 🟡 Not ready to close
> **Repos touched:** `repo-primary`

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🟡 |
| **Tests**          | 🟢 |
| **Security**       | 🟢 |
| **Code Quality**   | 🟡 |

> **Bottom line:** The GSC sync path is implemented and automated tests are green, but closure is blocked by real-property manual verification, owner approval, and stale setup/reference docs.

---

## 🔄 How the Feature Works (End-to-End)

```text
seo monitor sync
  -> Settings loads GSC_CREDENTIALS_PATH / GSC_PROPERTY_URL
  -> GscClient fetches query+page+date rows from GSC
  -> SeoRepository.upsert_search_console_record()
  -> SearchConsoleRecord rows in SQLite
  -> Rich summary table
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟢 Clean | repo-primary | GSC scope is read-only. [packages/core/src/nichefinder_core/sources/gsc_client.py:11](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/sources/gsc_client.py:11) |
| 🟢 Clean | repo-primary | Credentials path comes from settings/env, not hardcoded code. [packages/core/src/nichefinder_core/settings.py:98](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/settings.py:98), [packages/core/src/nichefinder_core/sources/gsc_client.py:23](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/sources/gsc_client.py:23) |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| GSC row mapping / empty response / credentials guard | ✅ Good | [tests/test_gsc_client.py:39](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_gsc_client.py:39) |
| Upsert-on-resync behavior | ✅ Good | [tests/test_gsc_client.py:113](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_gsc_client.py:113), [tests/test_cli_phase1.py:479](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_cli_phase1.py:479) |
| CLI empty-result / guard / summary paths | ✅ Good | [tests/test_cli_phase1.py:465](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_cli_phase1.py:465) |
| Full regression gate | ✅ Strong | `uv run pytest -q` -> `107 passed, 1 warning` |

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| GSC service-account adapter | ✅ Done | [packages/core/src/nichefinder_core/sources/gsc_client.py:15](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/sources/gsc_client.py:15) |
| `seo monitor sync` command | ✅ Done | [apps/cli/src/nichefinder_cli/commands/monitor.py:15](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/commands/monitor.py:15) |
| Update-on-resync repository logic | ✅ Done | [packages/db/src/nichefinder_db/crud.py:370](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/db/src/nichefinder_db/crud.py:370) |
| Settings fields | ✅ Done | [packages/core/src/nichefinder_core/settings.py:98](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/settings.py:98) |
| Manual real-property verification | ❌ Missing | [.platform/work/gsc-monitoring.md:42](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/gsc-monitoring.md:42) |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | Manual real-property verification is still unchecked. [.platform/work/gsc-monitoring.md:42](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/gsc-monitoring.md:42) |
| 2 | repo-primary | Closure is not owner-approved: `closure_approved: false`. [.platform/work/gsc-monitoring.md:13](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/gsc-monitoring.md:13) |
| 3 | repo-primary | `.env.example` is stale: it documents `GSC_SITE_URL` but code expects `GSC_CREDENTIALS_PATH` / `GSC_PROPERTY_URL`. [.env.example:7](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.env.example:7), [packages/core/src/nichefinder_core/settings.py:98](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/settings.py:98) |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | GSC domain context has stale adapter/dependency references. | [.platform/domains/gsc-monitoring.md:18](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/domains/gsc-monitoring.md:18) |
| 2 | repo-primary | `--days` has no lower bound; `0` or negative values can produce invalid ranges. | [apps/cli/src/nichefinder_cli/commands/monitor.py:17](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/commands/monitor.py:17) |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | Real GSC behavior cannot be proven without human GCP/service-account setup and a live property sync. |

---

## 🎯 Close Checklist / Priority Order

  □  1. 🔍  Run real `seo monitor sync` with credentials and confirm SQLite rows
  □  2. 🧾  Update `.env.example` and stale GSC domain references
  □  3. ✅  Get explicit owner closure approval and archive through the closure protocol
