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
updated_at: 2026-04-20
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
- [ ] The research pipeline can derive structured buyer problems before keyword expansion.
- [ ] Keyword generation uses buyer problems to create article-oriented keyword candidates instead of relying only on service-term prompts.
- [ ] Pre-SERP scoring separates article-fit from business-fit and rejects obvious directory/job-board/framework phrases.
- [ ] `uv run pytest` passes.
- [ ] Manual no-SERP verification shows the pipeline producing problem-led keyword ideas for a Montreal service seed.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-19 — Problem-first discovery should be a dedicated stream — it changes upstream keyword generation, not just the SERP shortlist.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-20 by danilulmashev
- **What just happened:** Replaced DDGS library-mediated fallback behavior with a direct DuckDuckGo HTML client that either returns real DDG results or marks DDGS as degraded/unavailable. Also updated overlap summaries to ignore degraded/nonpositive validations, so broken DDG runs cannot create false 3-source agreement or leak fallback-engine evidence into the support bundle.
- **Current focus:** —
- **Next action:** Have the user rerun the live Montreal pricing seed and confirm DDGS now either produces direct DuckDuckGo results or a clean unavailable/degraded bucket with no fallback contamination in article evidence or overlap tables.
- **Blockers:** none

## Progress log

2026-04-20 22:35 — Replaced DDGS library-mediated fallback behavior with a direct DuckDuckGo HTML client that either returns real DDG results or marks DDGS as degraded/unavailable. Also updated overlap summaries to ignore degraded/nonpositive validations, so broken DDG runs cannot create false 3-source agreement or leak fallback-engine evidence into the support bundle.

2026-04-20 22:28 — Added degraded-engine gating to the free validation pipeline: DDGS fallback backend responses are marked degraded in cached payloads, degraded validations are zeroed and blocked from article-evidence generation, and explicit question/quoted FAQ headings are separated from recurring headings with extra filtering for local one-off question patterns like Google Business Profile and Laval/Longueuil. Added regression tests for degraded payload handling and evidence suppression.

2026-04-20 22:13 — Applied a second support-bundle cleanup pass: recurring headings now require clearly informative quality, 'save money on' and 'questions to ask' agency headings are treated as generic noise, and secondary keyword phrases use a stricter phrase-quality score to drop fragments like 'how much', 'much web', and low-information local/generic combinations. Added regressions from the live Montreal pricing output.

2026-04-20 16:52 — Tightened free article-evidence quality filters to reduce support-bundle noise: removed generic reference/tier headings from recurring headings, restricted question bank to short query-aligned question-style headings, dropped heading-derived secondary keywords, and filtered numeric/year body phrases like '500 000' and 'montreal 2025'. Added regression tests from live Montreal pricing runs.

2026-04-20 16:27 — Implemented the audited free-pipeline hardening pass: atomic buyer-problem seed validation, frozen context replay for single-source runs, local search/article caching, buyer-problem article scraping, body-signal extraction, topic-family overlap summaries, and overlap-based shortlist confidence bonuses.

2026-04-20 16:03 — Added cross-engine overlap summaries for free validation; compare DDGS/Bing/Yahoo by exact query and surface repeated domains, secondary keywords, and questions from engine-backed article evidence.

2026-04-20 14:04 — Added Bing and Yahoo as bounded free research buckets alongside DDGS; free validation now prints per-source validation tables and scrapes bucket-backed articles into source-tagged keyword-bank evidence.

2026-04-20 13:21 — Extended the free-validation path to retain keyword-level DDGS evidence and scrape bounded DDGS-backed articles into recurring headings, question banks, and secondary-keyword suggestions.

2026-04-20 12:07 — Added a validate-free CLI command that runs buyer-problem discovery, deterministic scoring, Trends, and DDGS only, so shortlist quality can be calibrated without Tavily or SerpAPI.

2026-04-20 10:33 — Added bounded DDGS validation on top of deterministic scoring, Trends, and Tavily using shared external-evidence weighting and buyer-problem cross-checks.

## Open questions
- Should v0 rely only on first-party/local evidence plus Gemini synthesis, or do we want a curated public-source fetch layer in the same stream?

## Pinned follow-up
- Design and implement a better kickoff flow so the human does not need to invent SEO-quality seed keywords to start research.
- Add a CLI mode that accepts rough commercial/service phrasing and rescues it into buyer-problem research instead of treating it as the final target keyword.
- Evaluate a short guided interview flow for kickoff, with prompts like service, buyer type, local vs broad market, and goal (awareness, trust, leads).
- Add a `next article` discovery mode that proposes the strongest 2–3 article opportunities from business context plus accumulated research, instead of requiring a seed keyword.
- Add a `bad-seed rescue` mode that takes naive inputs like `find web developer in montreal` and transforms them into article-worthy subject families.
- Define the output bundle for kickoff modes: primary phrase, backup phrases, recurring support keywords, recurring questions, buyer problem, article angle, and confidence.
- Keep this as a follow-up to the current free-pipeline hardening work; do not let it block validation tuning.

---

## 🔍 Audit Report

_Status: not yet run_
