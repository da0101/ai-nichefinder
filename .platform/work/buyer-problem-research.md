---
stream_id: stream-buyer-problem-research
slug: buyer-problem-research
type: feature
status: in-progress
agent_owner: codex
domain_slugs: [buyer-problem-research]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/buyer-problem-research
created_at: 2026-04-19
updated_at: 2026-04-21
closure_approved: false
---

# buyer-problem-research

## Scope
- Build a buyer-problem-first discovery layer that generates structured problems before keyword suggestions.
- Keep v0 local-first and free/free-tier by default; no new paid search provider and no direct Google scraping.
- Replace “commercial-looking keyword” bias with article-fit plus business-fit heuristics.
- Persist enough structure in code/output so shortlisted keywords can be explained in terms of the buyer problem they came from.
- Out of scope: DB schema migrations, hosted services, or broad UI work.

## Done criteria
- [x] The research pipeline can derive structured buyer problems before keyword expansion.
- [x] Keyword generation uses buyer problems to create article-oriented keyword candidates instead of relying only on service-term prompts.
- [x] Pre-SERP scoring separates article-fit from business-fit and rejects obvious directory/job-board/framework phrases.
- [x] `uv run pytest` passes.
- [x] Manual no-SERP verification shows the pipeline producing problem-led keyword ideas for a Montreal service seed.
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-19 — Problem-first discovery should be a dedicated stream — it changes upstream keyword generation, not just the SERP shortlist.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-21 by codex
- **What just happened:** Added profile-scoped runtime isolation (`site_config`, DB, cache, outputs), expanded training memory to `noise` + `validity` + `legitimacy`, added `profile-*`, `review-training`, `approve-training`, `final-review`, and reset the default runtime state with `seo db reset --all-state`.
- **Current focus:** operator setup for two real business profiles
- **Next action:** create two profiles, configure each business separately, run 3-5 `validate-free` probes per profile, review/approve signals, then run `final-review <profile-a> <profile-b>`.
- **Blockers:** none

## Progress log

2026-04-21 13:06 — Added site-scoped learned-noise memory with automatic validate-free observation capture, review/approve CLI, and soft memory-aware demotions in pre-SERP scoring and article evidence.

2026-04-20 22:35 — Replaced DDGS library-mediated fallback behavior with a direct DuckDuckGo HTML client that either returns real DDG results or marks DDGS as degraded/unavailable. Also updated overlap summaries to ignore degraded/nonpositive validations, so broken DDG runs cannot create false 3-source agreement or leak fallback-engine evidence into the support bundle.

2026-04-21 12:10 — Tightened overlap/article-evidence recurrence to require real repetition, printed CLI source-health diagnostics, renamed persisted provenance to `gemini_problem`, and restored full-suite green at 93 passed. Manual Montreal `validate-free` reruns on 2026-04-20/21 are the no-paid verification evidence for this stream.

2026-04-21 13:35 — Added site-scoped learned-noise memory: `validate-free` now captures repeated keyword-phrase / secondary-phrase / weak-domain observations into local file-backed memory, `review-noise` prints repeated candidates, `approve-noise` promotes explicit suppressions, and approved memory feeds back into shortlist scoring plus article-evidence filtering. Focused suites passed at `27` and `12` tests.

2026-04-21 16:20 — Added multi-business profile isolation and full training review loop: active profile now controls separate `site_config`/DB/cache/outputs roots, training memory records `noise`, `validity`, and `legitimacy` separately, `review-training`/`approve-training`/`final-review` were added, focused pytest suites passed at `43`, and the default runtime was hard-reset with `uv run seo db reset --all-state`.

2026-04-20 22:28 — Added degraded-engine gating to the free validation pipeline: DDGS fallback backend responses are marked degraded in cached payloads, degraded validations are zeroed and blocked from article-evidence generation, and explicit question/quoted FAQ headings are separated from recurring headings with extra filtering for local one-off question patterns like Google Business Profile and Laval/Longueuil. Added regression tests for degraded payload handling and evidence suppression.

2026-04-20 22:13 — Applied a second support-bundle cleanup pass: recurring headings now require clearly informative quality, 'save money on' and 'questions to ask' agency headings are treated as generic noise, and secondary keyword phrases use a stricter phrase-quality score to drop fragments like 'how much', 'much web', and low-information local/generic combinations. Added regressions from the live Montreal pricing output.

2026-04-20 16:52 — Tightened free article-evidence quality filters to reduce support-bundle noise: removed generic reference/tier headings from recurring headings, restricted question bank to short query-aligned question-style headings, dropped heading-derived secondary keywords, and filtered numeric/year body phrases like '500 000' and 'montreal 2025'. Added regression tests from live Montreal pricing runs.

2026-04-20 16:27 — Implemented the audited free-pipeline hardening pass: atomic buyer-problem seed validation, frozen context replay for single-source runs, local search/article caching, buyer-problem article scraping, body-signal extraction, topic-family overlap summaries, and overlap-based shortlist confidence bonuses.

2026-04-20 16:03 — Added cross-engine overlap summaries for free validation; compare DDGS/Bing/Yahoo by exact query and surface repeated domains, secondary keywords, and questions from engine-backed article evidence.

2026-04-20 14:04 — Added Bing and Yahoo as bounded free research buckets alongside DDGS; free validation now prints per-source validation tables and scrapes bucket-backed articles into source-tagged keyword-bank evidence.

## Open questions
- Should v0 rely only on first-party/local evidence plus Gemini synthesis, or do we want a curated public-source fetch layer in the same stream?

## Audit follow-up — 2026-04-21

- The audit's red suite blocker is resolved: `uv run pytest -q` is green at `93 passed`.
- “Repeated” overlap fields, recurring headings, and question banks now require actual recurrence instead of falling back to singletons.
- CLI source-health output now makes degraded and unavailable engines explicit instead of forcing operators to infer that state from raw notes.
- The stream is now functionally at owner-review / closure-evidence stage; closure still requires explicit human sign-off.

## Pinned follow-up
- Design and implement a better kickoff flow so the human does not need to invent SEO-quality seed keywords to start research.
- Add a CLI mode that accepts rough commercial/service phrasing and rescues it into buyer-problem research instead of treating it as the final target keyword.
- Evaluate a short guided interview flow for kickoff, with prompts like service, buyer type, local vs broad market, and goal (awareness, trust, leads).
- Add a `next article` discovery mode that proposes the strongest 2–3 article opportunities from business context plus accumulated research, instead of requiring a seed keyword.
- Add a `bad-seed rescue` mode that takes naive inputs like `find web developer in montreal` and transforms them into article-worthy subject families.
- Define the output bundle for kickoff modes: primary phrase, backup phrases, recurring support keywords, recurring questions, buyer problem, article angle, and confidence.
- Keep this as a follow-up to the current free-pipeline hardening work; do not let it block validation tuning.

---

## 🔍 Audit — 2026-04-24

> Supersedes previous audit. Run via Stream / Feature Analysis Protocol — 6 parallel/rotated agents.

# 📋 Buyer Problem Research — Audit Snapshot

> **Stream:** `buyer-problem-research` · **Date:** 2026-04-24 · **Status:** 🟡 Not ready to close
> **Repos touched:** `repo-primary`

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🟡 |
| **Tests**          | 🟢 |
| **Security**       | 🟡 |
| **Code Quality**   | 🟡 |

> **Bottom line:** The core buyer-problem and free-validation pipeline is implemented and tests are green, but closure is blocked by remaining operator-profile setup, owner approval, mixed working-tree state, and one real viewer validation serialization bug.

---

## 🔄 How the Feature Works (End-to-End)

```text
seed / profile context
  -> buyer-problem discovery
  -> problem-led keyword expansion
  -> article-fit + business-fit pre-SERP scoring
  -> free validation + article evidence + overlap summaries
  -> training memory review/approval
  -> final review across profiles
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟢 Clean | repo-primary | Article fetching still routes through bounded source/scraper paths rather than direct Google scraping. [backend/packages/core/src/nichefinder_core/sources/scraper.py:47](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/sources/scraper.py:47) |
| 🟡 Medium | repo-primary | Local viewer mutating endpoints have no Origin/Content-Type guard if bound beyond localhost. [backend/apps/cli/src/nichefinder_cli/commands/viewer.py:10](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/commands/viewer.py:10), [backend/apps/cli/src/nichefinder_cli/viewer_server.py:351](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:351) |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| Buyer-problem discovery and keyword expansion | ✅ Strong | [tests/test_keyword_agent.py:120](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_keyword_agent.py:120) |
| Shortlist scoring / drift control / external validation | ✅ Good | [tests/test_keyword_agent.py:158](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_keyword_agent.py:158) |
| Profile commands, training approval, final review | ✅ Good | [tests/test_cli_phase1.py:349](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_cli_phase1.py:349) |
| Viewer `validate-free` real serialization | 🔴 None | [backend/apps/cli/src/nichefinder_cli/viewer_actions.py:132](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_actions.py:132) |
| Full regression gate | ✅ Strong | `uv run pytest -q` -> `107 passed, 1 warning` |

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| Structured buyer-problem discovery | ✅ Done | [backend/packages/core/src/nichefinder_core/agents/keyword_agent.py:65](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/agents/keyword_agent.py:65) |
| Problem-led keyword expansion | ✅ Done | [backend/packages/core/src/nichefinder_core/agents/keyword_agent.py:89](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/agents/keyword_agent.py:89) |
| Article-fit vs business-fit scoring | ✅ Done | [backend/packages/core/src/nichefinder_core/pre_serp.py:251](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/pre_serp.py:251) |
| Profile-scoped runtime isolation | ✅ Mostly done | [backend/apps/cli/src/nichefinder_cli/runtime.py:245](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/runtime.py:245) |
| Operator two-profile setup / final-review evidence | ❌ Missing | [.platform/work/buyer-problem-research.md:41](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/buyer-problem-research.md:41) |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | Viewer `validate-free` response serialization references `item.unavailable`, but `ExternalEvidenceValidation` has no such field. [backend/apps/cli/src/nichefinder_cli/viewer_actions.py:132](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_actions.py:132), [backend/packages/core/src/nichefinder_core/pre_serp_external.py:16](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/pre_serp_external.py:16) |
| 2 | repo-primary | Stream resume state still lists operator profile setup, 3-5 probes per profile, approval, and `final-review` as the next action. [.platform/work/buyer-problem-research.md:41](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/buyer-problem-research.md:41) |
| 3 | repo-primary | Closure is not owner-approved: `closure_approved: false`. [.platform/work/buyer-problem-research.md:13](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/buyer-problem-research.md:13) |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | `data/profiles/` runtime artifacts are untracked and not clearly ignored/owned. | [.gitignore:22](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.gitignore:22) |
| 2 | repo-primary | LangGraph Tavily path appears to unpack `apply_tavily_validation()` as 2 values while the helper returns 3. | [backend/packages/core/src/nichefinder_core/orchestrator/graph.py:76](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/orchestrator/graph.py:76) |
| 3 | repo-primary | Several touched files exceed the ~300-line guideline. | [backend/packages/core/src/nichefinder_core/free_article_evidence.py:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/packages/core/src/nichefinder_core/free_article_evidence.py:1), [backend/apps/cli/src/nichefinder_cli/runtime.py:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/runtime.py:1) |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | The pinned kickoff / bad-seed / next-article items are follow-up work, not blockers for this stream. |

---

## 🎯 Close Checklist / Priority Order

  □  1. 🐛  Fix real viewer `validate-free` serialization and add coverage
  □  2. 🔍  Complete and record the two-profile operator validation loop
  □  3. ✅  Reconcile branch/working-tree ownership, then request owner closure approval
