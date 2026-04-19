---
domain_id: dom-data-architecture
slug: data-architecture
status: active
repo_ids: [repo-primary]
related_domain_slugs: []
created_at: 2026-04-19
updated_at: 2026-04-19
---

# data-architecture

_Metadata rules: `domain_id` must be `dom-<slug>`, `slug` must match the filename, `repo_ids` should name the repos this domain touches, and `updated_at` should change whenever contracts or touch-points change._

## What this domain does

Defines the persistent data contracts that every future agent family depends on: collection, analysis, content, distribution, and monitoring. The outcome is a schema that can store richer SEO evidence without forcing repeated breaking rewrites as the platform grows into the six-agent design.

## Backend / source of truth

- SQLModel entities, repository methods, and migrations are the source of truth.
- Lifecycle state, freshness, locale, score provenance, and formula versioning belong in persisted records rather than transient agent memory.
- New provider and agent integrations should persist typed data into first-class tables, not opaque blobs where avoidable.
- The first V2 slice is additive: extend existing Phase 1 entities and repository methods before introducing wholly new agent-family tables.

## Frontend / clients

- CLI workflows that read and write keyword, brief, article, ranking, and usage records.
- The local viewer, which depends on stable persisted entity shapes for inspection.
- Future monitoring and orchestration modes, which will rely on resumable, typed persisted state.

## API contract locked

- Keyword and monitoring records must support locale, freshness, provenance, and lifecycle state explicitly.
- Opportunity scoring should be versioned and persisted as a first-class record, not only as an overwritten scalar on `Keyword`.
- New agent families should be able to persist outputs without schema-breaking rewrites across the rest of the platform.
- Data-model changes must preserve the currently working Phase 1 CLI flows or include a deliberate migration path.
- Local SQLite upgrades must be additive and non-destructive; `seo db init` should be enough to create or extend the schema for this phase.

## Data Model V2 — Target Schema

### Implemented (this branch)

| Entity | Table | Status | Key V2 additions |
|---|---|---|---|
| `Keyword` | `keyword` | ✅ live | lifecycle_status, locale, market, freshness timestamps (metrics/serp/trend/score), provenance (metrics_source, trend_source, score_source, score_formula_version) |
| `OpportunityScoreRecord` | `opportunityscorerecord` | ✅ live | formula_version, score_source, input_snapshot_json — full score history, not just latest scalar |
| `ContentBriefRecord` | `contentbriefrecord` | ✅ live | schema_version, score_record_id, run_id, agent_version, model_id |
| `SerpResult` | `serpresult` | ✅ live | schema_version, provider, locale, market, run_id, agent_version, model_id |
| `SearchConsoleRecord` | `searchconsolerecord` | ✅ live | First-class GSC ingestion: query, page_url, impressions, clicks, ctr, position, snapshot_date, property_id, data_source |
| `AnalyticsRecord` | `analyticsrecord` | ✅ live | First-class GA4 ingestion: page_url, sessions, bounce_rate, avg_session_duration_sec, record_date, property_id, data_source |

### Existing (Phase 1, unchanged)

| Entity | Table | Notes |
|---|---|---|
| `KeywordCluster` / `KeywordClusterMembership` | `keywordcluster`, `keywordclustermembership` | Grouping by seed term prefix |
| `Article` / `ArticleVersion` | `article`, `articleversion` | Content lifecycle + version history |
| `CompetitorPage` | `competitorpage` | SERP competitor content analysis |
| `RankingSnapshot` | `rankingsnapshot` | Article-level rank check (position + page) |
| `PerformanceRecord` | `performancerecord` | Legacy article-level impressions/clicks; prefer `SearchConsoleRecord` for new GSC ingestion |
| `ApiUsageRecord` | `apiusagerecord` | Provider call count + spend tracking per month |

### Staged (next phases)

| Entity | Purpose | Blocking |
|---|---|---|
| `SourceRegistry` | Typed registry of data sources (GSC property, GA4 property, SerpAPI key) with credentials ref and quota tracking | GSC/GA4 provider client implementation |
| `ProviderRun` | One row per provider fetch run — ties `SearchConsoleRecord`/`AnalyticsRecord` batches back to a single fetch event with status, row count, error | Monitoring reliability and retry logic |
| Distribution-agent entities | Article publish targets, syndication status | Phase 3 distribution agent family |

## Key files

- `packages/core/src/nichefinder_core/models/`
- `packages/db/src/nichefinder_db/models.py`
- `packages/db/src/nichefinder_db/crud.py`
- `packages/db/src/nichefinder_db/migrations.py`
- `packages/db/alembic/`
- `apps/cli/src/nichefinder_cli/workflows.py`
- `docs/seo-platform-gap-analysis-roadmap.md`

## Decisions locked

- Data-model work comes before deeper orchestration work.
- Schema changes should extend the current local-first CLI foundation, not replace it.
- First-party monitoring and provider clients should land on top of typed persisted contracts, not ad hoc JSON blobs.
- Existing working Phase 1 flows remain compatibility targets during this phase.
- The initial V2 migration slice persists keyword metadata and score history first; deeper entity expansion can follow once the base contracts are stable.
