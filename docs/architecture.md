# Architecture

## Current Scope

The current codebase is intentionally CLI first. The goal is to make keyword
research workflows reliable before adding FastAPI or a web dashboard.

## Initial Package Boundaries

- `nichefinder-core`
  - Environment configuration
  - Shared Pydantic models
  - Future service orchestration
- `nichefinder-db`
  - SQLAlchemy metadata
  - Session factory
  - Bootstrap helpers
  - Alembic migration environment
- `nichefinder-cli`
  - Operator commands
  - Research workflow entrypoints

## Locale Strategy

- Primary market profile: Montreal, Quebec, Canada
- Primary language: French
- Secondary language: English
- The system should keep language and market explicit on every keyword, rather
  than assuming a global locale

## Scoring Direction

- `serp_difficulty`: raw page-one competitiveness
- `site_rankability`: personalized fit for your own domain and niche position
- `demand_score`: composite score using Google Ads buckets, Trends, Autocomplete,
  and PAA signals

