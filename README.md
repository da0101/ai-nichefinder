# AI Nichefinder

CLI-first SEO intelligence tooling for personal niche research, starting with
French-language Montreal and Quebec opportunities, then English expansion
across North America.

## Why This Exists

This project helps a solo operator find blog topics and keyword opportunities
that are actually rankable for a low-authority personal site. The initial niche
focus is restaurant SaaS / restaurant technology, with a strategy that treats
Montreal and Quebec as French-first markets and the rest of North America as
primarily English.

The product starts as a local CLI because the hard part is not the interface.
The hard part is building a trustworthy research workflow around free data
sources, caching, SERP inspection, and honest scoring.

## Current Scope

Phase 0 is complete. The repository currently includes:

- A `uv` Python workspace
- A Typer CLI entrypoint
- Shared settings and environment handling
- SQLAlchemy models and database bootstrap
- Alembic migration scaffolding
- Dockerized PostgreSQL for local development

The external data-source integrations are not wired yet. The current commands
exist to validate project structure, configuration loading, and local
development flow.

## Stack Choices

- `Python`: best fit for API orchestration, scoring, parsing, and automation
- `Typer`: clean CLI workflows for a CLI-first MVP
- `PostgreSQL`: durable storage for keywords, SERP snapshots, and rank history
- `SQLAlchemy + Alembic`: explicit models and versioned schema evolution
- `Docker Compose`: local PostgreSQL without host-machine drift
- `uv`: fast dependency and workspace management

## Workspace Layout

- `apps/cli`: Typer-based operator workflow
- `packages/core`: settings, shared models, and research services
- `packages/db`: SQLAlchemy models, session handling, and Alembic
- `infra`: local infrastructure and environment templates
- `docs`: architecture, scoring, and setup notes
- `data`: cache and export output directories kept out of git

## Quick Start

### Prerequisites

- Python `3.12+`
- `uv`
- Docker Desktop or Docker Engine with Compose

### Local Setup

1. Copy `infra/env/.env.example` to `infra/env/.env`
2. Start PostgreSQL:

```bash
docker compose -f infra/docker-compose.yml up -d
```

3. Install workspace dependencies:

```bash
uv sync
```

4. Inspect config and credential readiness:

```bash
uv run --package nichefinder-cli nichefinder status
```

5. Create local tables:

```bash
uv run --package nichefinder-cli nichefinder db init
```

### Useful Commands

```bash
uv run --package nichefinder-cli nichefinder --help
uv run --package nichefinder-cli nichefinder status
uv run --package nichefinder-cli nichefinder keywords discover "logiciel commande en ligne restaurant"
```

## Product Direction

- CLI first, no auth
- Free-tier data sources only
- Raw SERP difficulty and personalized site rankability tracked separately
- Store Google Ads buckets and trends signals separately instead of fake exact
  search volume

## Planned Integrations

- Google Autocomplete for keyword expansion
- Google Trends for relative demand comparisons
- Google Ads Keyword Planner for volume buckets
- Serper.dev and Google Programmable Search for SERP analysis
- Google Search Console for post-publication performance tracking
- Gemini for content brief generation and clustering support

## What Is Still Missing

- API credentials
- Seed keywords
- Portfolio and blog URLs
- Implemented source adapters
- Scoring and enrichment pipelines
- Scheduled rank tracking jobs

## Documentation

- Architecture notes: [docs/architecture.md](docs/architecture.md)
- Setup checklist: [docs/setup-checklist.md](docs/setup-checklist.md)
