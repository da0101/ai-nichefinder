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
