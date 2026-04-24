---
stream_id: stream-reddit-api-integration
slug: reddit-api-integration
type: feature
status: blocked
agent_owner: codex
domain_slugs: [keyword-research]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/reddit-api-integration
created_at: 2026-04-21
updated_at: 2026-04-21
closure_approved: false
---

# reddit-api-integration

## Scope
- Add Reddit as an official read-only enrichment source for buyer-problem and article-brief research.
- Use the approved Reddit Data API path with OAuth and a descriptive User-Agent; do not rely on raw HTML scraping.
- Keep Reddit as a supporting evidence source for repeated pain points, language patterns, and question discovery rather than a primary ranking validator.
- Fit the integration into the existing local-first CLI workflow with cache-aware, rate-limited retrieval and small structured outputs.
- Out of scope: posting, commenting, voting, moderation actions, Devvit app work, or model training on Reddit data.

## Done criteria
- [ ] Reddit API access is approved and the required credentials are available locally.
- [ ] A read-only Reddit source module can fetch public posts/comments relevant to shortlisted topics.
- [ ] Reddit outputs are summarized into structured buyer-signal/question/phrase evidence suitable for the brief pipeline.
- [ ] Tests pass for the Reddit source and integration path.
- [ ] Manual verification shows Reddit-derived evidence improving brief quality without polluting keyword validation.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-21 — Treat Reddit as a read-only enrichment source, not a primary keyword validator — forum discussion quality is valuable for pain-point discovery but should not override SERP evidence.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-21 by codex
- **What just happened:** Submitted Reddit API access request for an external non-Devvit local research tool use case.
- **Current focus:** Wait for Reddit approval while keeping the integration explicitly tracked.
- **Next action:** When Reddit responds, wire credentials into local settings and implement a read-only Reddit source module plus brief-enrichment outputs.
- **Blockers:** Waiting for Reddit Data API approval response.

## Progress log
2026-04-21 11:00 — Created the stream after submitting a Reddit Data API access request for ai-nichefinder's external read-only research workflow.

## Open questions
- Which subreddits should be included in the initial allowlist for business/SEO/web-development topic enrichment?
- How much raw Reddit text, if any, should be cached locally versus summarized immediately into structured evidence?

---

## 🔍 Audit — 2026-04-24

> Run via Stream / Feature Analysis Protocol — 6 parallel/rotated agents.

# 📋 Reddit API Integration — Audit Snapshot

> **Stream:** `reddit-api-integration` · **Date:** 2026-04-24 · **Status:** 🔴 Blocked / not ready to close
> **Repos touched:** `repo-primary`

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🔴 |
| **Tests**          | 🔴 |
| **Security**       | 🟡 |
| **Code Quality**   | 🟡 |

> **Bottom line:** No Reddit API integration code exists yet; current Reddit behavior is only legacy SERP-domain scoring for `reddit.com`.

---

## 🔄 How the Feature Works (End-to-End)

```text
Current:
SERP result pages -> estimate_difficulty() -> reddit.com treated as high-authority domain

Missing target:
Reddit OAuth settings -> Reddit Data API client -> posts/comments fetch
  -> structured buyer evidence -> brief enrichment
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟡 Medium | repo-primary | Reddit OAuth credentials are not modeled in settings/env yet. [packages/core/src/nichefinder_core/settings.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/settings.py:27), [.env.example:4](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.env.example:4) |
| 🟢 Clean | repo-primary | No hardcoded Reddit secrets found; no Reddit client exists yet to leak tokens. |
| 🟡 Medium | repo-primary | Existing generic HTML search User-Agent is browser-like, not a descriptive Reddit API User-Agent. [packages/core/src/nichefinder_core/sources/html_search_engine.py:13](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/sources/html_search_engine.py:13) |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| Legacy SERP Reddit domain scoring | ✅ Good | [tests/test_serp_signals.py:54](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_serp_signals.py:54) |
| Reddit API source/client | 🔴 None | Missing |
| Reddit OAuth/settings readiness | 🔴 None | Missing |
| Reddit posts/comments parsing | 🔴 None | Missing |
| Reddit buyer-signal/brief enrichment | 🔴 None | Missing |

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| Stream registration | ✅ Done | [.platform/work/reddit-api-integration.md:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/reddit-api-integration.md:1) |
| Reddit API approval/credentials | ❌ Blocked | [.platform/work/reddit-api-integration.md:26](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/reddit-api-integration.md:26) |
| Reddit source module | ❌ Missing | [apps/cli/src/nichefinder_cli/runtime.py:26](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/runtime.py:26) |
| Reddit service wiring | ❌ Missing | [apps/cli/src/nichefinder_cli/runtime.py:64](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/runtime.py:64) |
| Reddit enrichment in research pipeline | ❌ Missing | [apps/cli/src/nichefinder_cli/workflows.py:98](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/workflows.py:98) |
| Legacy Reddit SERP scoring | ✅ Existing, not this integration | [packages/core/src/nichefinder_core/utils/serp_signals.py:4](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/utils/serp_signals.py:4) |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | Stream done criteria are all unchecked and `closure_approved: false`. [.platform/work/reddit-api-integration.md:13](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/reddit-api-integration.md:13), [.platform/work/reddit-api-integration.md:25](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/reddit-api-integration.md:25) |
| 2 | repo-primary | No Reddit API client/source exists and DI has no Reddit service slot. [apps/cli/src/nichefinder_cli/runtime.py:26](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/runtime.py:26) |
| 3 | repo-primary | Research pipeline has DDGS/Bing/Yahoo/Tavily validation paths but no Reddit enrichment bucket. [apps/cli/src/nichefinder_cli/workflows.py:98](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/apps/cli/src/nichefinder_cli/workflows.py:98) |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | Add Reddit settings with local-secret handling, readiness check, rate/budget limits, and descriptive User-Agent. | [packages/core/src/nichefinder_core/settings.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/settings.py:27) |
| 2 | repo-primary | Add structured evidence fields/path for buyer signals, questions, phrases, and source URLs without treating Reddit as primary keyword validation. | [packages/core/src/nichefinder_core/agents/synthesis_agent.py:129](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/agents/synthesis_agent.py:129) |
| 3 | repo-primary | Keep new Reddit code out of already-large files. | [packages/core/src/nichefinder_core/pre_serp_external.py:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/packages/core/src/nichefinder_core/pre_serp_external.py:1) |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | Current branch is `feature/serp-pipeline-fix`; no local `feature/reddit-api-integration` branch was observed. |
| 2 | Existing Reddit code mention is only `reddit.com` as a SERP domain signal, not Reddit Data API access. |

---

## 🎯 Close Checklist / Priority Order

  □  1. 🔐  Get Reddit Data API approval and local credentials
  □  2. ⚙️  Add Reddit settings/env handling, cache/rate limits, and read-only source client
  □  3. 🧪  Add tests for fetch, parsing, error/rate handling, and brief evidence integration
  □  4. ✅  Run manual verification, update decisions/log, and request owner closure approval
