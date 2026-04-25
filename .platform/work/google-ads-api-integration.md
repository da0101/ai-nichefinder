---
stream_id: stream-google-ads-api-integration
slug: google-ads-api-integration
type: feature
status: planning
agent_owner: codex
domain_slugs: [keyword-research]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/google-ads-api-integration
created_at: 2026-04-21
updated_at: 2026-04-21
closure_approved: false
---

# google-ads-api-integration

## Scope
- Add a Google Ads API integration path for keyword and market-intent enrichment where it materially improves research quality.
- Keep the integration optional and explicitly credential-gated rather than assumed by default.
- Fit Google Ads signals into the current shortlist/validation pipeline without overwhelming the existing free and paid evidence layers.
- Preserve local-first execution and clear spend visibility for any credentialed Ads usage.
- Out of scope: campaign management, ad creation, bid automation, or turning ai-nichefinder into an advertising tool.

## Done criteria
- [ ] The intended Google Ads API use cases and required metrics are defined clearly.
- [ ] Local credential/config handling is implemented safely and remains optional.
- [ ] A source module can retrieve the approved Google Ads keyword/planning signals needed by the research pipeline.
- [ ] Tests pass for the integration path.
- [ ] Manual verification shows the Ads signals improving triage or briefing quality without breaking the free-first workflow.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-21 — Track Google Ads API as a dedicated future stream instead of mixing it into buyer-problem research — it is a separate source-integration concern with its own credential, cost, and product-scope questions.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-21 by codex
- **What just happened:** Created a dedicated tracking stream so the Google Ads API integration does not get lost behind current buyer-problem work.
- **Current focus:** Keep the stream visible until the team decides when to start design and implementation.
- **Next action:** Define the concrete use cases, metrics, and credential requirements before opening implementation work.
- **Blockers:** Not yet prioritized; no implementation work started.

## Progress log
2026-04-21 11:00 — Created the stream to keep Google Ads API integration visible in active work tracking.

## Open questions
- Which Google Ads API endpoints or planner signals are actually worth integrating for ai-nichefinder?
- Should Ads data influence shortlist scoring directly or be reserved for later-stage validation only?

---

## 🔍 Audit — 2026-04-24

> Run via Stream / Feature Analysis Protocol — 6 parallel/rotated agents.

# 📋 Google Ads API Integration — Audit Snapshot

> **Stream:** `google-ads-api-integration` · **Date:** 2026-04-24 · **Status:** 🔴 Planning only / not ready to close
> **Repos touched:** `repo-primary`

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🔴 |
| **Tests**          | 🔴 |
| **Security**       | 🟡 |
| **Code Quality**   | 🟡 |

> **Bottom line:** The stream is tracked but not implemented; there is no Google Ads API source/client/settings path yet, and use cases/metrics are still undefined.

---

## 🔄 How the Feature Works (End-to-End)

```text
Current:
SERP + Trends -> AdsAgent estimates ad signals from stored SERP ads
  -> synthesis consumes ad-snippet-derived output

Missing target:
Google Ads credentials -> official Ads API source client
  -> approved keyword/planning metrics -> shortlist/validation/brief signal
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟢 Clean | repo-primary | No Google Ads credentials or hardcoded Ads secrets found. |
| 🟡 Medium | repo-primary | Optional credential gating is missing because settings have no Google Ads developer-token/customer/login fields. [backend/core/src/nichefinder_core/settings.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/settings.py:27) |
| 🟡 Medium | repo-primary | `.env.example` documents no Google Ads variables. [.env.example:4](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.env.example:4) |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| Existing pipeline injection of `ads_agent` stub | 🟡 Thin | [tests/test_cli_phase1.py:834](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_cli_phase1.py:834), [tests/test_graph.py:109](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_graph.py:109) |
| Google Ads settings / credential readiness | 🔴 None | No test found |
| Google Ads API client parsing / errors / budget gating | 🔴 None | No source module found |
| Ads API integration into shortlist/validation/brief quality | 🔴 None | No implementation or manual evidence |

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| Stream registration | ✅ Done | [.platform/work/google-ads-api-integration.md:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/google-ads-api-integration.md:1) |
| Use cases and required metrics | ❌ Missing | [.platform/work/google-ads-api-integration.md:26](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/google-ads-api-integration.md:26) |
| Optional local credential/config handling | ❌ Missing | [backend/core/src/nichefinder_core/settings.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/settings.py:27) |
| Official Google Ads dependency/client | ❌ Missing | [backend/core/pyproject.toml:6](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/pyproject.toml:6) |
| Google Ads source module | ❌ Missing | `backend/core/src/nichefinder_core/sources/` |
| Existing ad-snippet agent | ✅ Existing, not this feature | [backend/core/src/nichefinder_core/agents/ads_agent.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/agents/ads_agent.py:27) |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | Define exact Google Ads use cases, endpoints, and metrics before implementation. [.platform/work/google-ads-api-integration.md:49](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/google-ads-api-integration.md:49) |
| 2 | repo-primary | Add safe optional Google Ads config/readiness fields and `.env.example` placeholders. [backend/core/src/nichefinder_core/settings.py:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/settings.py:27) |
| 3 | repo-primary | Add an official Google Ads source adapter and mocked tests; current `AdsAgent` only reads SERP ad snippets. [backend/core/src/nichefinder_core/agents/ads_agent.py:30](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/agents/ads_agent.py:30) |
| 4 | repo-primary | Add budget/rate/usage accounting for Ads calls. [.platform/conventions/data-sources.md:27](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/conventions/data-sources.md:27) |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | Rename or split current `AdsAgent` semantics when official Google Ads arrives; today “ads” means SERP ad-snippet analysis. | [backend/core/src/nichefinder_core/agents/ads_agent.py:22](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/core/src/nichefinder_core/agents/ads_agent.py:22) |
| 2 | repo-primary | Keep the integration source-specific and out of Typer command logic per domain contract. | [.platform/domains/keyword-research.md:31](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/domains/keyword-research.md:31) |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | Existing `AdsAgent` is not Google Ads API integration. It derives signals from SerpAPI ad payloads. |

---

## 🎯 Close Checklist / Priority Order

  □  1. 🎯  Define approved use cases and metrics
  □  2. 🔐  Add optional credential/settings/env handling with no default-on paid behavior
  □  3. 🧪  Add Google Ads source adapter with mocked parser/error/budget tests
  □  4. 🔗  Wire signals into shortlist/validation or briefing with explainable weighting
  □  5. ✅  Run manual validation, update decisions/log, and request owner closure approval
