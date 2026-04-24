# ai-nichefinder — Decision Log

Last updated: 2026-04-19

> **Purpose:** capture the _why_ behind architectural, product, and tooling decisions so future AI sessions and developers don't have to re-derive them (or undo them).

---

## Format

Each decision is one row. **Locked** decisions are final until a new decision supersedes them. **Deferred** decisions are explicit non-decisions with a trigger for when to revisit.

| # | Date | Status | Topic | Decision | Why | Rejected alternatives |
|---|---|---|---|---|---|---|

---

## Locked decisions

_Decisions that are final. If you want to change one of these, write a new decision row that supersedes it — don't silently overwrite._

| # | Date | Topic | Decision | Why | Rejected alternatives |
|---|---|---|---|---|---|
| 1 | 2026-04-17 | Primary surface | Keep the product CLI-first and local-first for Phase 1. | The operator is one person, iteration speed matters more than hosting, and there is no need to pay the complexity cost of a web app yet. | FastAPI/web UI, background workers, hosted multi-user product |
| 2 | 2026-04-17 | Persistence | Use SQLite plus filesystem outputs as the default source of truth. | Local durability is enough for the current workflow and keeps setup friction low while drafts remain easy to inspect manually. | PostgreSQL, remote DB, opaque managed storage |
| 3 | 2026-04-17 | Paid model usage | Gemini is the only paid service that may be assumed enabled by default right now. | The user explicitly accepts Gemini spend but wants the rest of the stack to stay free or free-tier for now. | Broad paid-tool adoption, default-on DataForSEO, default-on extra model vendors |
| 4 | 2026-04-17 | Google-safe acquisition | Do not add direct Google scraping; use sanctioned APIs, free-tier tools, and robots-respecting page fetches instead. | Ranking research is only useful if the project stays within techniques that avoid bans and long-term risk. | `google.com/search` scraping, bypassing robots, aggressive fetch loops |
| 5 | 2026-04-17 | Publication gate | Generated content must pass through human review before it is considered final or published. | AI makes writing easy; the actual product value comes from judgment about relevance, accuracy, and fit for the site. | Auto-publish workflows, treating raw model output as production-ready |
| 6 | 2026-04-18 | Phase 1 boundary | Phase 1 closes on a reliable local CLI workflow for research → brief → draft → approve → publish → rank/report/budget; the full 6-agent platform remains a later roadmap target. | Without a hard boundary, the stream becomes unfinishable because it keeps absorbing future architecture work. | Treating the full 6-agent system as Phase 1, leaving the stream scope implicit |
| 7 | 2026-04-18 | Robots failure policy | Fail closed when `robots.txt` cannot be fetched, with an explicit operator override to fail open for controlled local use. | Crawl safety should default to the conservative behavior; if robots retrieval fails, scraping should stop unless the operator intentionally accepts the risk. | Silent fail-open behavior, hard-coded fail-open with no override, bypassing robots errors entirely |
| 8 | 2026-04-19 | Free-source metric gaps | Use neutral fallback scores for missing volume and difficulty when the keyword source is free-source discovery (`gemini_serpapi`), instead of treating missing metrics as worst-case values. | The local workflow must still reach brief and draft generation on real discovered keywords even when paid keyword metrics are unavailable; otherwise the pipeline looks healthy but never creates artifacts. | Blocking all unknown-metric keywords, treating unknowns as zero volume or max difficulty, inventing fake numeric metrics |
| 9 | 2026-04-19 | Branch policy | Use `develop` as the default integration branch, keep `main` as the release branch, and branch all new feature work from `develop`. | This separates day-to-day development from release promotion and makes the intended merge path explicit for both humans and agents. | Continuing single-branch development on `main`, branching features directly from `main`, release work without a dedicated integration branch |
| 10 | 2026-04-19 | Repo hygiene baseline | Keep one canonical env template at the repo root and remove dormant docker/dev scaffolding when it no longer backs a real workflow. | Duplicate setup files and abandoned infra stubs create false surfaces, drift quickly, and make onboarding harder than the actual local-first CLI requires. | Mirrored env templates, keeping dormant docker compose files "just in case", preserving stale duplicate architecture docs |
| 11 | 2026-04-19 | Data Model V2 migration shape | Start Data Model V2 with additive schema extensions plus a persisted opportunity-score history table, and preserve existing Phase 1 reads/writes while local SQLite upgrades run through `seo db init`. | This unlocks lifecycle, locale, freshness, provenance, and score versioning now without forcing a destructive DB reset or a full rewrite of viewer/CLI flows before provider work can start. | Big-bang schema replacement, JSON-only score persistence, destructive local DB reset as the default upgrade path |
| 12 | 2026-04-19 | Pre-SERP keyword gating | Choose the SerpAPI shortlist with a deterministic pre-score based on intent, business fit, local/buyer language, duplicate collapse, and exact-match GSC history when available, instead of using Gemini output order. | SerpAPI is the paid validation bottleneck, so candidates need an explainable cheap gate before live SERP spend; pure LLM ordering is too opaque and too wasteful. | Using Gemini to pick the shortlist, validating every keyword with SerpAPI, requiring a second Google-derived provider before SerpAPI |
| 13 | 2026-04-19 | Buyer-problem-first discovery | Generate structured buyer problems before keyword expansion, using first-party GSC query evidence when available, and derive keyword candidates from those problems instead of from raw service-term variations. | “Commercial-looking” keywords were still overproducing unwinnable hire/framework queries; problem-first generation gives the pipeline a more article-fit starting point without adding a new paid source. | Continuing service-term-first keyword expansion, relying on the shortlist scorer alone to fix poor candidates, adding a new search provider before first using existing GSC evidence |
| 14 | 2026-04-20 | Viewer frontend | Replace the inline HTML/JS viewer with a React 18 + Vite + shadcn/ui dashboard at `apps/dashboard/`. Built `dist/` committed to git; Python server serves it with fallback to inline HTML. | Vanilla HTML in a Python string is not evolvable — can't add live polling, search, or future control features. React + shadcn/ui enables 30s live refresh, a filterable sidebar, and a foundation for future agent-control UI. | Keeping vanilla HTML, server-sent events without React, full separate web service |
| 15 | 2026-04-20 | External keyword evidence layering | Validate shortlisted buyer-problem keywords with bounded external evidence in this order: deterministic scoring → Trends → Tavily → DDGS → SERP, with each external source weighted below seed fidelity and drift controls. | Free and free-tier sources should add reassurance before paid SERP calls, but they must not be allowed to re-promote drifted cost/service variants over the original buyer question. | Letting Tavily/DDGS drive ranking directly, using DDGS as a Google replacement, jumping from deterministic scoring straight to SERP |
| 16 | 2026-04-20 | Multi-engine research buckets | Supersedes #15. Treat DDGS, Bing, and Yahoo as separate bounded research buckets before paid validation, in this order: deterministic scoring → Trends → DDGS → Bing → Yahoo → Tavily → SERP. Their role is research enrichment and article discovery, not Google-truth validation, and their weights stay below seed fidelity and drift controls. | The operator wants richer free research before spending on Tavily or SerpAPI. Separate engine buckets increase phrase, heading, and article coverage while keeping a clear boundary between free aggregation and final Google-facing checks. | Letting Bing/Yahoo override ranking directly, using Bing/Yahoo as a proxy for Google SERP truth, skipping free buckets and paying for every candidate |
| 17 | 2026-04-21 | GSC resync dedupe | Keep Search Console duplicate prevention application-level for Phase 1 by upserting on `(query, page_url, snapshot_date, property_id)` in the repository, and defer a schema-level uniqueness migration until it is justified by real concurrent-writer pressure. | The current product is a single-operator local CLI with a single sync path; the upsert logic already preserves the rolling-finalization behavior GSC needs, while a schema migration would add risk and migration work without solving a live user problem yet. | Immediate DB uniqueness migration, append-only GSC rows, skipping updates on resync |
| 18 | 2026-04-21 | Learned noise memory | Keep repeated-run noise learning local, site-scoped, file-backed, and approval-based: `validate-free` records observations automatically, `review-noise` surfaces repeated candidates, and only `approve-noise` entries affect scoring/evidence via soft demotions. | This makes the research pipeline portable across services without silently hardcoding one niche or overfitting from a single noisy run, and it avoids a DB migration while the learning loop is still being validated. | Automatic self-learning suppressions, global cross-site blacklists, immediate SQLite schema migration for learning memory |
| 19 | 2026-04-21 | Multi-business training isolation | Isolate runtime state per business profile under `data/profiles/<slug>/` and expand learning memory into three approval-based signal classes: `noise`, `validity`, and `legitimacy`. | Training two businesses in one repo is only safe if DB, cache, site config, and learned signals are separated; otherwise one business silently contaminates the other and the operator cannot trust review output. | One shared DB/cache for all businesses, noise-only learning, global positive/negative memory across businesses |
| 20 | 2026-04-22 | Viewer interaction boundary | Expand the localhost viewer from read-only inspection to a limited testing workspace that may switch profiles, edit profile config, approve training signals, create profiles, and trigger `validate-free`, but not publish content or mutate ranking/content records directly. | The operator needs a browser surface to test multiple SEO profiles comfortably, but the viewer still must stay local-first and avoid becoming an uncontrolled admin surface. | Keeping the browser fully read-only, building a separate web backend, allowing arbitrary write operations from the dashboard |
| 21 | 2026-04-24 | REST control plane | Expose app functionality through typed REST actions and allowlisted jobs, not arbitrary shell command execution. | The same local API surface can support the React dashboard, automation, and future cloud deployment; arbitrary shell execution would become remote code execution once hosted. | Generic `/shell` or `/command` endpoint, one-off endpoints that bypass runtime/profile isolation, blocking long-running workflows inside request handlers |
| 22 | 2026-04-24 | REST job persistence | Persist REST job status, params, results, errors, and timestamps in SQLite via `JobRecord` instead of keeping job state only in process memory. | Browser polling, local automation, and future cloud workers need stable task ids whose completed outcomes remain inspectable after the local server restarts. | In-memory-only job registry, filesystem JSON job logs, blocking long-running workflows inside request handlers |
| 23 | 2026-04-24 | REST write guard | Protect mutating REST endpoints with a token-or-loopback policy: default localhost writes are limited to loopback clients and loopback browser origins, and any configured `VIEWER_API_TOKEN` becomes mandatory bearer auth for all writes. | This keeps local testing simple while closing the obvious cloud/CSRF failure modes and preventing a reverse-proxy loopback hop from silently bypassing auth once a token is configured. | Open localhost writes, loopback-only checks with no token mode, building a full multi-user auth system before the first local/cloud-safe slice |

---

## Deferred decisions

_Explicit non-decisions. Each has a trigger for when to revisit._

| # | Date | Topic | Current non-decision | Trigger to revisit |
|---|---|---|---|---|
| 1 | 2026-04-17 | OpenAI support | OpenAI is not part of Phase 1, but may be added later as an optional model provider. | Revisit when Gemini-only coverage blocks a workflow or quality target. |
| 2 | 2026-04-17 | LinkedIn optimization | LinkedIn profile improvement is interesting, but not yet part of the core blog-ranking workflow. | Revisit after the blog workflow proves useful or when personal-brand optimization becomes a top priority. |
| 3 | 2026-04-17 | Hosted deployment | There is no decision to host, sync, or multi-user-enable this project yet. | Revisit only if localhost CLI usage becomes a real bottleneck. |

---

## How to add a decision

1. Use the highest unused `#`.
2. Fill date, status, topic, decision, why, rejected alternatives.
3. If this supersedes a prior decision, reference it: "Supersedes #N".
4. If it's deferred, include a trigger condition.
5. Commit with message: `Record decision #N: <topic>`.
