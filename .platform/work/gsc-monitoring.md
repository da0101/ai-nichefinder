---
stream_id: stream-gsc-monitoring
slug: gsc-monitoring
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [gsc-monitoring]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/gsc-monitoring
created_at: 2026-04-19
updated_at: 2026-04-19
closure_approved: false
---

# gsc-monitoring

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope

- Implement a Google Search Console API v1 adapter (`gsc_client.py`) that authenticates via OAuth2 and fetches impression/click/CTR/position rows for a configured property.
- Wire the adapter to `SeoRepository.save_search_console_record()` to populate the existing `SearchConsoleRecord` table.
- Expose a `seo monitor sync` CLI command (Typer) that runs the fetch + persist cycle for a configurable date range (default: last 7 days).
- Add settings fields for GSC credentials path and property URL.
- Write integration tests using a mock HTTP layer (no real API calls in CI).
- Out of scope: GA4/AnalyticsRecord, automated scheduling, real-time data, rank-change alerting.

## Done criteria

**GCP prerequisite (human steps before manual verification):**
- Create GCP project, enable Search Console API v1.
- Create service account, download JSON key, add the SA email as a Full User on the GSC property `sc-domain:danilulmashev.com`.
- Set `GSC_CREDENTIALS_PATH=/path/to/key.json` and `GSC_PROPERTY_URL=sc-domain:danilulmashev.com` in `.env`.

- [ ] `gsc_client.py` adapter authenticates via service account credentials and fetches `SearchConsoleRecord`-shaped rows from GSC API.
- [ ] `seo monitor sync [--days N] [--property URL]` CLI command works end-to-end: fetch → upsert → persist → Rich summary table.
- [ ] Re-syncing the same date range updates existing rows (impressions/clicks/ctr/position) rather than inserting duplicates.
- [ ] Settings load `GSC_CREDENTIALS_PATH` and `GSC_PROPERTY_URL` from `.env` (never hardcoded).
- [ ] At least 5 unit tests cover: API row mapping, empty-result handling, update-on-resync, credentials guard (no path → clear error), CLI upsert path.
- [ ] `pytest` full suite still passes (no regressions).
- [ ] Manual verification: after GCP prerequisite steps, `seo monitor sync` runs locally and rows appear in SQLite (blocked on human GCP setup).
- [ ] `.platform/memory/log.md` appended.
- [ ] `decisions.md` updated if any architectural choices were made.

## Key decisions

_Append-only. Format: `YYYY-MM-DD — <decision> — <rationale>`_

2026-04-19 — GSC-only stream (no GA4) — keeps scope tight; GA4 is a separate client with different auth and data shape.
2026-04-19 — Use `google-api-python-client` + `google-auth-oauthlib` — official Google client, well-maintained, handles token refresh automatically.
2026-04-19 — Update-on-resync (not skip) by composite key (query + page_url + snapshot_date + property_id) — GSC finalizes metrics over a ~2-3 day rolling window; skipping freezes stale numbers from the first sync.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 by danilulmashev (auto)
- **What just happened:** (auto) b049ad1: feat: Rich spinner on every waiting step during seo research
- **Current focus:** —
- **Next action:** (auto-saved from commit — update next action manually)
- **Blockers:** none

## Progress log

_Append-only._

2026-04-19 16:11 — (auto) b049ad1: feat: Rich spinner on every waiting step during seo research

2026-04-19 16:04 — (auto) c217749: fix: pytrends 429 graceful fallback, remove score cap, informational seeds

2026-04-19 15:55 — (auto) 7a80d71: feat: real-time console feedback during seo research pipeline

2026-04-19 13:54 — (auto) 505ff0f: feat: Montreal-focused SEO targeting — location wired end-to-end, seeds updated

2026-04-19 13:42 — (auto) 1abddc4: docs: add CLI cheat sheet

2026-04-19 13:37 — (auto) a9a9c92: feat(db): auto-backup before init, backup/export commands, WAL mode

2026-04-19 13:25 — (auto) 72f6544: feat(gsc-monitoring): GSC adapter, upsert, monitor sync CLI (53 tests pass)

2026-04-19 13:22 — (auto) a396ce1: Register gsc-monitoring stream: domain file, stream file, ACTIVE.md, BRIEF.md

2026-04-19 — Stream registered; domain file created; branch feature/gsc-monitoring created from develop.

## Open questions

_Things blocked on user input. Remove when resolved._
