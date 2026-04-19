# Data Source Conventions

Last updated: 2026-04-17

## Allowed source policy

- Gemini is the only paid service assumed enabled by default right now.
- Other sources must stay free or free-tier unless the user explicitly opts into additional spend.
- No direct `google.com/search` scraping.
- Competitor or rewrite scraping is allowed only when robots permit it and rate limits remain conservative.

## Current source mix

| Source | Role | Cost stance | Notes |
|---|---|---|---|
| Gemini | synthesis, classification, briefing, drafting | paid allowed | primary LLM for Phase 1 |
| SerpAPI | SERP results and query expansion | free-tier / tightly budgeted | monthly call cap enforced via settings |
| Pytrends | trend signals | free | no secret required |
| Website fetches via Playwright | competitor/rewrite content extraction | free | robots + delay + limiter required |

## Built-in limits from code

| Client / action | Limit |
|---|---|
| SerpAPI | 10 calls / 60s plus monthly call cap from settings |
| Generic scraper | 5 fetches / 30s plus randomized delay |
| Gemini Flash | 15 calls / 60s |
| Gemini Pro | 2 calls / 60s |

## Review checklist for any new source

- Is it free or free-tier, or did the user explicitly approve paid usage?
- Is it consistent with Google-safe acquisition?
- Does it have a single adapter wrapper instead of leaking into commands?
- Does it update usage or budget accounting if it can incur cost?
- Does it need a new invariant recorded in `decisions.md`?
