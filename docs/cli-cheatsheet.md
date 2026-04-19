# SEO CLI Cheat Sheet

All commands use `uv run seo <command>` if the venv isn't activated,
or just `seo <command>` after `source .venv/bin/activate`.

---

## Setup

```bash
# First time / after DB loss
seo db init

# Open local viewer at http://127.0.0.1:8765
seo view
```

---

## Core Research Workflow

```bash
# Full pipeline: keyword → SERP → trend → scoring → brief prompt
seo research "web development agency"

# Run pipeline on all seed_keywords from data/site_config.json
seo research-batch

# SERP-only analysis for a keyword (no full pipeline)
seo serp "hire web developer"

# Generate a content brief for a keyword (by ID)
seo brief <keyword-id>

# Write an article draft from a brief
seo write <keyword-id>

# Rewrite a published article
seo rewrite https://danilulmashev.com/your-post
```

---

## Keywords

```bash
# List all discovered keywords
seo keywords list

# Cluster keywords by root term
seo keywords cluster

# Inspect a single keyword and its pipeline state
seo keywords inspect <keyword-id>
```

---

## Articles

```bash
# List all generated articles and their status
seo articles list

# Approve a draft for publishing
seo articles approve <article-id>

# Mark an article as published (required before it's tracked)
seo publish <article-id> https://danilulmashev.com/your-post
```

---

## Rank Tracking

```bash
# Check current rankings for all published articles
seo rank check

# Alias for check
seo rank sync
```

---

## GSC Monitoring

> Requires GCP setup — see prerequisites below.

```bash
# Sync last 7 days of GSC data (impressions, clicks, position)
seo monitor sync

# Sync a custom date range
seo monitor sync --days 30

# Sync a specific GSC property
seo monitor sync --property sc-domain:danilulmashev.com
```

**GCP prerequisites (one-time human setup):**
1. Create GCP project → enable Search Console API v1
2. Create service account → download JSON key
3. Add the service account email as a Full User on the GSC property
4. Add to `.env`:
   ```
   GSC_CREDENTIALS_PATH=/path/to/key.json
   GSC_PROPERTY_URL=sc-domain:danilulmashev.com
   ```

---

## Reporting & Budget

```bash
# Top 10 opportunities by score
seo report

# API call counts and spend (Gemini, SerpAPI)
seo budget

# Overall status summary
seo status
```

---

## Database

```bash
# Init DB (auto-backs up existing DB first)
seo db init

# Manual backup → data/db/backups/seo.db.TIMESTAMP.bak
seo db backup

# Export all keywords + articles to data/exports/export-TIMESTAMP.json
seo db export
```

> **Habit:** run `seo db export` after every research session.
> JSON exports survive any DB issue and accumulate in `data/exports/`.

---

## Site Config

```bash
# Interactive prompt to update site_config.json
seo config
```

---

## Typical Session

```bash
source .venv/bin/activate

seo db backup                              # snapshot before working
seo research "web development toronto"
seo research "hire react developer"
seo keywords list                          # review scores
seo brief <keyword-id>                     # generate brief for best candidate
seo write <keyword-id>                     # draft the article
seo articles list                          # review status
seo articles approve <article-id>          # human sign-off
seo publish <article-id> https://...       # mark as published
seo db export                              # save portable backup
```
