---
stream_id: stream-phase-1-foundation
slug: phase-1-foundation
type: feature
status: done
agent_owner: codex-cli
domain_slugs: [keyword-research, content-production, rank-tracking]
repo_ids: [repo-primary]
base_branch: main
git_branch: feature/phase-1-foundation
created_at: 2026-04-17
updated_at: 2026-04-19
closure_approved: true
---

# phase-1-foundation

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope
- Make the existing local CLI loop reliable end to end: research → brief → draft → approve → publish → rank/report/budget.
- Define what "rankable enough to write" means for this project using the current local source mix and scoring workflow.
- Keep all source usage within Google-safe, low-cost boundaries that fit the current budget rules.
- Preserve human approval before content is treated as final or published.
- Produce enough tests and manual verification evidence that this stream can be closed on local workflow quality rather than aspirational architecture.

## Phase 1 boundary
- This stream is **not** the full 6-agent platform from the long architecture prompt.
- This stream closes when the current local SEO workflow is coherent, testable, and safe to use for real topic selection and draft generation.
- The larger platform remains the target roadmap in `docs/seo-platform-gap-analysis-roadmap.md`.
- Explicitly out of scope for this stream: GSC/GA4 ingestion, the technical audit agent, the distribution/presence agent, Reddit/Stack Overflow question discovery, Common Crawl intelligence, Data Model V2, and full LangGraph checkpoint/resume orchestration.
- Also still out of scope: hosted productization, LinkedIn automation, and OpenAI integration.

## Done criteria
- [x] Phase 1 has explicit acceptance criteria tied to the real CLI commands and data outputs.
- [x] `nichefinder research "<seed>"` stores keywords in SQLite and prints a ranked opportunity view with score and priority.
- [x] `nichefinder brief <keyword-id>` stores a `ContentBriefRecord` containing the target keyword, secondary keywords, suggested title, H2 structure, questions, tone, CTA type, and word-count target.
- [x] `nichefinder write <keyword-id>` creates both an `Article` row and a markdown draft under `outputs/articles/`.
- [x] `nichefinder articles approve <article-id>` followed by `nichefinder publish <article-id> <url>` preserves the human gate, and `publish` fails for a non-approved article.
- [x] `nichefinder rank check`, `nichefinder report`, and `nichefinder budget` run against local data and persist or display the expected local ranking/usage evidence.
- [x] Source policy is explicit and enforced enough that new work cannot silently drift into direct Google scraping, hidden paid providers, or unsafe crawl behavior.
- [x] The robots failure policy is decided, implemented, and covered by tests.
- [x] Direct CLI tests cover `research` and at least one ranking/report path in addition to `publish`.
- [x] `pytest` passes for the touched areas.
- [x] Manual verification covers at least one realistic seed topic and confirms the resulting DB rows and filesystem outputs.
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-17 — Seed this stream during activation — the user identified Phase 1 completion as the first active workstream.
2026-04-18 — Narrow Phase 1 to the current local workflow — the full 6-agent platform remains the roadmap, not this stream’s closure target.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 by danilulmashev
- **What just happened:** Re-audited Phase 1 after the live brief/write verification and viewer work. The acceptance criteria now appear satisfied, the audit snapshot was refreshed in the stream file, and the stream status was moved to awaiting-verification.
- **Current focus:** stream closure complete
- **Next action:** Start the next stream around first-party monitoring and post-publish feedback.
- **Blockers:** none

## Progress log
2026-04-19 09:10 — Owner approved stream closure. Phase 1 was marked complete and the platform docs were updated for archival.
2026-04-19 08:00 — Re-audited Phase 1 after the live brief/write verification and viewer work. The acceptance criteria now appear satisfied, the audit snapshot was refreshed in the stream file, and the stream status was moved to awaiting-verification.

2026-04-19 07:34 — Added a dependency-free local web viewer command, plus read-only dashboard/detail endpoints over SQLite so research, SERP analysis, competitor pages, briefs, and article previews can be inspected in a browser. Verified the server boots and added viewer data tests.

2026-04-19 07:25 — Implemented neutral fallback scoring for free-source keywords, added 'keywords inspect' for stored research artifacts, hardened competitor scraping to skip timeout failures, and validated live brief/write on a discovered keyword.

2026-04-19 06:35 — Verified the live runtime, fixed stale Gemini defaults plus two real workflow bugs, and proved that research/report/budget/rank work on live data; the remaining blocker is that free-source keywords still have no volume/difficulty so briefs are never created.

2026-04-19 06:35 — Updated Gemini defaults to working 2.5 models, fixed `pytrends` empty-topic handling and competitor datetime serialization, and ran live `research` / `brief` / `report` / `budget` / `rank check`.
2026-04-19 06:14 — Re-audited the stream, anchored a fresh 2026-04-19 audit snapshot, and confirmed closure is blocked by live env setup plus missing real manual workflow evidence.

2026-04-19 00:12 — Re-audited the stream after the robots/test hardening work; confirmed the remaining blockers are local runtime setup and missing manual workflow evidence.
2026-04-18 22:50 — Implemented fail-closed robots behavior with an explicit override, added CLI tests for research and report, and passed the full pytest suite.

2026-04-18 23:05 — Implemented fail-closed robots behavior with an explicit override and added direct CLI tests for `research` plus `report`; `uv run pytest` passed.
2026-04-18 22:31 — Turned Phase 1 into a concrete execution contract with explicit scope, exclusions, and command-level acceptance criteria.

## Open questions
- Is the next stream after Phase 1 `data-model-v2`, `gsc-monitoring`, or a combined monitoring-foundation stream?

---

## 🔍 Audit — 2026-04-19

> Supersedes previous audit. Run via Stream / Feature Analysis Protocol — 1 parallel analysis pass.

# 📋 Phase 1 Foundation — Audit Snapshot

> **Stream:** `phase-1-foundation` · **Date:** 2026-04-19 · **Status:** 🟡 Awaiting verification
> **Repos touched:** repo-primary

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🟢 |
| **Tests**          | 🟢 |
| **Security**       | 🟢 |
| **Code Quality**   | 🟡 |

> **Bottom line:** Phase 1 now appears functionally complete for its narrowed CLI-first scope; the remaining gap to closure is owner verification plus closure bookkeeping, not a missing workflow step.

---

## 🔄 How the Feature Works (End-to-End)

```text
seed keyword
  ↓
research command
  ↓
KeywordAgent
  ├─ Gemini keyword expansion
  ├─ SerpAPI related searches
  └─ Gemini intent labeling
  ↓
keyword rows in SQLite
  ↓
SERP + trend + ads + competitor analysis
  ↓
SynthesisAgent opportunity score + content brief
  ↓
ContentAgent draft markdown + article row
  ↓
articles approve / publish
  ↓
rank check + report + budget
  ↓
local viewer (dashboard + keyword inspection)
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟢 Clean | repo-primary | `publish` still enforces the human gate and rejects non-approved articles before any publication state change. `backend/apps/cli/src/nichefinder_cli/main.py:136`; `tests/test_cli_publish.py:36` |
| 🟢 Clean | repo-primary | Robots handling remains fail-closed by default and scraping still routes through the explicit robots checker. `backend/packages/core/src/nichefinder_core/settings.py:45`; `backend/packages/core/src/nichefinder_core/sources/scraper.py:40`; `tests/test_sources.py:27` |
| 🟢 Clean | repo-primary | Secrets stay env-loaded via `Settings`; the new local viewer is read-only and does not add write-side HTTP mutations. `backend/packages/core/src/nichefinder_core/settings.py:10`; `backend/apps/cli/src/nichefinder_cli/viewer_server.py:174` |
| 🟢 Clean | repo-primary | The competitor fetch path now skips scrape failures instead of crashing the brief pipeline, which reduces failure amplification without weakening robots enforcement. `backend/packages/core/src/nichefinder_core/agents/competitor_agent.py:42`; `tests/test_competitor_agent.py:72` |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| Keyword discovery filtering and persistence | ✅ Good | `tests/test_keyword_agent.py` |
| SERP parsing and budget enforcement | ✅ Good | `tests/test_serp_agent.py` |
| Scraper, robots, and trend edge cases | ✅ Good | `tests/test_sources.py` |
| Opportunity scoring fallback and rankable cap | ✅ Good | `tests/test_synthesis_agent.py` |
| Competitor scraping serialization and timeout-skipping | ✅ Good | `tests/test_competitor_agent.py` |
| Content draft generation | ✅ Good | `tests/test_content_agent.py` |
| CLI command surface (`research`, `report`, `publish`) | ✅ Good | `tests/test_cli_phase1.py`, `tests/test_cli_publish.py` |
| Local viewer data payloads | ✅ Good | `tests/test_viewer_data.py` |
| End-to-end workflow orchestration (`run_full_pipeline`, `check_rankings`) | 🔴 None | — |
| Direct CLI coverage for `brief`, `write`, and `rank check` | 🟡 Thin | live verification only; no dedicated CLI tests |

> **Current test result:** `uv run pytest -q` → `23 passed, 1 warning`

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| Research command and pipeline orchestration | ✅ Done | `backend/apps/cli/src/nichefinder_cli/main.py:48`; `backend/apps/cli/src/nichefinder_cli/workflows.py:15` |
| Brief generation and persisted `ContentBriefRecord` | ✅ Done | `backend/apps/cli/src/nichefinder_cli/main.py:101`; `backend/apps/cli/src/nichefinder_cli/workflows.py:73` |
| Article drafting with DB row + markdown output | ✅ Done | `backend/apps/cli/src/nichefinder_cli/main.py:113`; `backend/apps/cli/src/nichefinder_cli/workflows.py:104`; `backend/packages/core/src/nichefinder_core/agents/content_agent.py:102` |
| Approval and publish gating | ✅ Done | `backend/apps/cli/src/nichefinder_cli/commands/articles.py:30`; `backend/apps/cli/src/nichefinder_cli/main.py:136` |
| Rank/report/budget command surface | ✅ Done | `backend/apps/cli/src/nichefinder_cli/commands/ranks.py:14`; `backend/apps/cli/src/nichefinder_cli/main.py:157`; `backend/apps/cli/src/nichefinder_cli/main.py:186` |
| Unknown-metric fallback for free-source keywords | ✅ Done | `backend/packages/core/src/nichefinder_core/agents/synthesis_agent.py:33`; `backend/packages/core/src/nichefinder_core/settings.py:33` |
| Local inspection surface for stored work | ✅ Done | `backend/apps/cli/src/nichefinder_cli/commands/keywords.py:58`; `backend/apps/cli/src/nichefinder_cli/viewer_server.py:174` |
| LangGraph-based orchestrator scaffold | ⚪ Deferred | `backend/packages/core/src/nichefinder_core/orchestrator/graph.py:15` |
| Real local workflow evidence in SQLite + filesystem | ✅ Done | `data/db/seo.db`; `outputs/articles/ai-product-development-roadmap-consulting-for-startups-your-guide-to-strategic-growth-funding.md` |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | None for Phase 1 closure; the stream now appears blocked only on owner verification and closure protocol steps. |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | `brief`, `write`, and `rank check` still lean on live/manual evidence more than direct CLI tests, so closure confidence is strong but not fully symmetric across the command surface. | `backend/apps/cli/src/nichefinder_cli/main.py:101`; `backend/apps/cli/src/nichefinder_cli/main.py:113`; `backend/apps/cli/src/nichefinder_cli/commands/ranks.py:14` |
| 2 | repo-primary | The workflow still depends on Gemini for major judgment calls such as intent labeling, SERP competition interpretation, gap detection, and briefing; deterministic scoring exists, but calibration against first-party search data is still missing. | `backend/packages/core/src/nichefinder_core/agents/keyword_agent.py:41`; `backend/packages/core/src/nichefinder_core/agents/serp_agent.py:31`; `backend/packages/core/src/nichefinder_core/agents/competitor_agent.py:68` |
| 3 | repo-primary | The orchestration layer is still a scaffold and the CLI paths bypass it; there is no persisted checkpoint/resume or true multi-agent runtime yet. | `backend/packages/core/src/nichefinder_core/orchestrator/graph.py:15`; `backend/packages/core/src/nichefinder_core/orchestrator/state.py:4`; `backend/apps/cli/src/nichefinder_cli/workflows.py:15` |
| 4 | repo-primary | The legacy `briefs generate` placeholder remains in the tree and is not part of the mounted command surface. | `backend/apps/cli/src/nichefinder_cli/commands/briefs.py:8` |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | The current source stack is still narrow: Gemini + SerpAPI + Pytrends + robots-respecting page fetches. It is enough for Phase 1, but not the full intelligence layer for highest-confidence topic judgment. |
| 2 | There is no Search Console, GA4, Bing Webmaster, Reddit/Stack Exchange question discovery, or Common Crawl integration in the current code path. |
| 3 | Ranking checks only verify whether a published URL appears in current SERP results; they do not ingest first-party clicks, impressions, CTR, or average position. |
| 4 | The long-term 6-agent platform remains roadmap-only; the current LangGraph graph is a local scaffold rather than the active product surface. |

---

## 🎯 Close Checklist / Priority Order

  □  1. ✅  Confirm the stream’s done criteria against the now-persisted brief, article row, and markdown output.
  □  2. ✅  Present the live evidence: 1 stored brief, 1 stored article, 141 keywords, and 23 passing tests.
  □  3. 🔍  Decide with the owner whether the remaining thin CLI-test areas are acceptable for Phase 1 closure.
  □  4. ✅  If the owner agrees, keep the stream in `awaiting-verification` and run the closure protocol rather than adding out-of-scope roadmap work.
  □  5. ⚪  Spin the next stream around monitoring/data-collection foundations (`gsc-monitoring`, `data-model-v2`, or a combined monitoring-foundation stream).
