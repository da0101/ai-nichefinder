# ai-nichefinder — Architecture

Last updated: 2026-04-19

> Local-first SEO research and content workflow CLI for `danilulmashev.com`, optimized for finding topics worth writing before spending time generating articles.

---

## 1. What this system does

The operator runs a Typer CLI locally to research keywords, inspect SERP conditions, generate content briefs and draft articles, and track whether published pieces gain search positions. The product goal is not "generate more text"; it is "generate content only when there is evidence the topic is worth pursuing."

Technically, the CLI composes a set of local services around a SQLite database, filesystem outputs, and a handful of external providers. Commands orchestrate keyword discovery, SERP/trend/competitor analysis, Gemini synthesis, article drafting, and ranking snapshots while tracking API usage and enforcing rate limits.

**Who uses it:** Daniil as the single local operator
**Who deploys it:** manual local execution only
**Hosting target:** localhost CLI on one machine, plus an optional local viewer/testing workspace

## 2. High-level components

```
┌────────────────────┐
│ Typer CLI commands │
└─────────┬──────────┘
          │
          v
┌────────────────────┐
│ Runtime bootstrap  │  loads Settings + SiteConfig + DB session
└─────────┬──────────┘
          │
          v
┌────────────────────────────────────────────────────┐
│ Service container                                  │
│ Gemini • SerpAPI • Trends • Scraper • Agents       │
└─────────┬──────────────────────────────────────────┘
          │
          ├─────────────── external requests ───────────────┐
          v                                                 v
┌────────────────────┐                           ┌────────────────────┐
│ SQLite + SQLModel  │                           │ External providers │
│ keywords/articles/ │                           │ Gemini / SerpAPI / │
│ briefs/ranks/usage │                           │ Trends / websites  │
└─────────┬──────────┘                           └────────────────────┘
          │
          v
┌────────────────────┐                           ┌────────────────────┐
│ Filesystem outputs │                           │ Local viewer HTTP  │
│ drafts/reports/etc │                           │ server + JSON APIs │
└────────────────────┘                           └────────────────────┘
```

## 3. Tech stack (summary)

| Layer | Choice | Notes |
|---|---|---|
| Language(s) | Python 3.12 | Workspace split across `apps/cli`, `packages/core`, `packages/db` |
| Framework(s) | Typer, LangGraph, Pydantic v2, SQLModel | Rich is the terminal UI layer |
| Build tool(s) | `uv`, Ruff, pytest | No containerized app runtime required |
| Data store(s) | SQLite + local filesystem | Database defaults to `data/db/seo.db` |
| Hosting | Local machine only | CLI-first, with an optional localhost viewer/testing workspace |
| CI/CD | None yet | Manual local execution and verification |

Per-stack conventions live in `conventions/{stack}.md`.

## 4. Data flow

1. A CLI command loads `.env`-backed settings, `data/site_config.json`, and a DB session.
2. Runtime wiring builds API/source clients plus domain agents.
3. Research workflows call source adapters for SERP, trends, optional paid keyword metrics, and competitor pages.
4. Agents normalize those signals into `Keyword`, `SerpResult`, `CompetitorPage`, `ContentBriefRecord`, `Article`, `RankingSnapshot`, and `ApiUsageRecord` rows.
5. Generated article content is also written to filesystem outputs so drafts remain inspectable outside the database.
6. CLI commands render tables or structured output for the operator, who decides whether to approve or publish.
7. The optional local viewer serves dashboard/testing pages backed by the same SQLite data and markdown outputs, and may perform low-risk local actions such as switching profiles, saving profile config, approving training signals, and triggering `validate-free`.

## 5. Auth model

There is no end-user auth layer yet. The trust boundary is the local machine: whoever can run the CLI and read `.env` controls the project. Secrets live in `.env`, publication remains manual, and no automated external side effects should be added without an explicit review of safety and spend.

See `conventions/security.md` for auth-adjacent details.

## 6. External services

| Service | What it's used for | Where the secret lives |
|---|---|---|
| Google Gemini | synthesis, intent labeling, briefs, article drafting | `.env` via `GOOGLE_GEMINI_API_KEY` |
| SerpAPI | Google SERP result retrieval and PAA/related query extraction | `.env` via `SERPAPI_KEY` |
| Pytrends | trend signals | no secret required |
| Target websites via Playwright | competitor/rewrite content fetches when robots allow it | no stored secret |

## 7. Deploy topology

There is no multi-environment deployment topology yet. The system is developed and run locally. Promotion today means "change code locally, run the CLI locally, inspect outputs locally." The lightweight viewer is also local-only and should not be treated as a hosted product surface. If a future hosted service appears, that will require a new architecture decision and deployment convention rather than being inferred from the current code.

See `conventions/deployment.md` for the local release and rollback playbook.

## 8. Cross-component invariants

The things that must stay true as the system evolves. Breaking any of these is a hard fail.

1. The CLI remains the primary user surface until a deliberate product decision changes that.
2. The system optimizes for ranking potential and usefulness, not for maximizing AI-generated output volume.
3. Gemini is the only paid service that may be assumed safe to use by default right now; everything else must stay free or free-tier unless the user opts in.
4. No workflow may introduce Google-bannable behavior such as direct Google scraping or aggressive page fetching.
5. Human approval remains required before AI-generated content is treated as final or published.
6. Local SQLite plus filesystem outputs remain the source of truth until a migration plan is explicitly approved.

## 9. Known architectural debt

| Area | Issue | Planned fix |
|---|---|---|
| Phase 1 scope | The original "large prompt" goals are not yet mapped to concrete acceptance criteria in repo docs. | Turn Phase 1 into explicit stream-level milestones. |
| Source strategy | Older docs still mention services not reflected in the current code path. | Keep `.platform/` as source of truth and reconcile legacy docs when touched. |
| Metrics feedback loop | Ranking snapshots and local inspection exist, but richer first-party performance feedback is still shallow. | Add Search Console and GA4-backed measurement in a later phase. |
