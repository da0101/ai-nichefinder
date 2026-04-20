---
domain_id: dom-buyer-problem-research
slug: buyer-problem-research
status: active
repo_ids: [repo-primary]
related_domain_slugs: [keyword-research, content-production]
created_at: 2026-04-19
updated_at: 2026-04-19
---

# buyer-problem-research

## What this domain does

Finds real buyer problems that can turn into rankable article opportunities before the system spends scarce SERP budget. It sits upstream of keyword research: if this stage is weak, the pipeline keeps proposing commercially flavored but unwinnable queries.

## Backend / source of truth

- Buyer-problem discovery should stay local-first and free/free-tier by default.
- `KeywordAgent` and related prompts are the current generation layer and will need a problem-first precursor.
- Pre-SERP scoring should separate `article fit` from `business fit` before any SerpAPI call is made.
- First-party evidence can come from `SearchConsoleRecord`, ranking history, and existing content performance when available.
- Public-source research must obey `conventions/data-sources.md`: no direct Google scraping and all page fetches must respect robots and rate limits.

## Frontend / clients

- `nichefinder research <seed>` should eventually expose which buyer problems were identified before keyword scoring begins.
- `nichefinder keywords inspect <keyword-id>` should remain able to explain why a keyword was shortlisted, including its problem context.
- The local viewer may later show problem clusters and rejection reasons, but that is not required for v0.

## API contract locked

- No keyword should reach the paid SERP validation stage without an explainable article-fit and business-fit rationale.
- Buyer problems must be represented as structured records in memory/output, not only as prompt text.
- V0 must not require a new paid provider or direct Google scraping.

## Key files

- `apps/cli/src/nichefinder_cli/workflows.py`
- `packages/core/src/nichefinder_core/agents/keyword_agent.py`
- `packages/core/src/nichefinder_core/gemini/prompts.py`
- `packages/core/src/nichefinder_core/pre_serp.py`
- `packages/core/src/nichefinder_core/models/site.py`
- `packages/db/src/nichefinder_db/crud.py`

## Decisions locked

- Research starts from buyer problems, not from raw service-keyword variations.
- Article-rankability and business-fit are separate gates.
- Paid SERP validation is the final check, not the first meaningful filter.
