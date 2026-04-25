---
domain_slug: gsc-monitoring
title: GSC Monitoring
owner: claude-code
status: active
created_at: 2026-04-19
---

# Domain: GSC Monitoring

Google Search Console integration — fetches post-publish performance signals (impressions, clicks, CTR, position) and persists them into `SearchConsoleRecord` rows so the pipeline can close the feedback loop.

## Cross-layer touch-points

| Layer | Component | Role |
|---|---|---|
| CLI | `backend/apps/cli` → `seo monitor sync` | Entry point; triggers the GSC fetch + persist cycle |
| Adapter | `backend/core/.../adapters/gsc_client.py` | OAuth2 credentials + Google Search Console API v1 calls |
| Core models | `SearchConsoleRecord` (tracking.py) | Target persistence entity — already exists in schema |
| DB / repo | `SeoRepository.save_search_console_record()` | Already implemented; just needs a caller |
| Migration | `backend/db/.../migrations.py` | Table already created via V2 migration |
| Config | `.env` / `site_config.json` | GSC property URL, credentials path |

## External dependencies

- Google Search Console API v1 (`google-api-python-client`, `google-auth-oauthlib`)
- OAuth2 credentials JSON from Google Cloud Console (offline access, read-only scope)
- Property: `sc-domain:danilulmashev.com` (already verified)

## Invariants

- Credentials file path must come from settings/env — never hardcoded.
- Sync is additive — re-syncing the same date range upserts, not duplicates.
- CLI command is read-only with respect to site content; it only writes to DB.
- Rate limits: GSC API default quota is 1200 QPM — no throttle needed for single-site use.

## Out of scope

- GA4 (Google Analytics 4) — separate stream.
- Real-time GSC data — API exposes data with ~2 day lag; daily snapshot is sufficient.
- Automated scheduling — cron/daemon integration is a later stream.
