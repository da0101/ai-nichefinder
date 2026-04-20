---
stream_id: stream-serp-pipeline-fix
slug: serp-pipeline-fix
type: feature
status: in-progress
agent_owner: codex
domain_slugs: [keyword-research]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/serp-pipeline-fix
created_at: 2026-04-19
updated_at: 2026-04-20
closure_approved: false
---

# serp-pipeline-fix

## Problem

One keyword research session burns 78 SerpAPI calls against a free tier of 250/month.
That means 3 research sessions exhausts the entire monthly budget.

The root cause is two code paths calling SerpAPI far more than necessary:

### Root cause 1 — Redundant SerpAPI expansion (`keyword_agent.py:65-68`)

After Gemini generates up to 50 keyword ideas (free), the code loops over 5 of those
terms and calls `serpapi_client.get_related_searches()` on each — burning 5 SerpAPI calls
just to get more keyword ideas that Gemini could have generated for free.

```python
# keyword_agent.py lines 65-68 — THE WASTE
serp_queries = list(dict.fromkeys(expanded_terms))[: min(5, payload.max_keywords)]
for term in serp_queries:
    related = await self.serpapi_client.get_related_searches(term, location=...)
    expanded_terms.extend(related)
```

### Root cause 2 — Uncapped parallel SERP analysis (`graph.py:57`)

The parallel analysis node runs a SerpAPI call for every single discovered keyword,
up to 50. This is 1 SerpAPI call per keyword × 50 keywords = 50+ calls per session.
Most of these keywords are minor variations of each other and don't need individual SERP data.

```python
# graph.py line 57 — THE EXPLOSION
results = await asyncio.gather(*[analyze(keyword_id) for keyword_id in state["discovered_keyword_ids"]])
```

### Root cause 3 — Prompts don't know the real goal

`KEYWORD_EXPANSION_PROMPT` in `prompts.py` says "personal technical consulting site" and
asks for "informational and commercial opportunities." It does not know that the goal is:
**attract Montreal business owners who are ready to hire a developer.**

The prompts generate too many informational/dev-facing keywords ("multi-tenancy patterns",
"unit testing best practices") and not enough transactional local keywords ("hire web
developer montreal", "how much does an app cost montreal").

---

## Goal

Reduce SerpAPI calls from ~78 to ≤10 per research session without losing research quality.
Refocus keyword discovery on local commercial intent: Montreal business owners who are
ready to hire, not developers learning about tech.

**Before:** 78 calls × free tier 250 = 3 sessions/month
**After:** ≤10 calls × free tier 250 = 25+ sessions/month

---

## Exact Changes

### Change 1 — `packages/core/src/nichefinder_core/agents/keyword_agent.py`

**Delete lines 65-68** (the SerpAPI expansion loop). Replace with nothing — Gemini's
output is already sufficient. The function `_expand_with_free_sources` should return
`expanded_terms` directly after the Gemini call, without calling SerpAPI at all.

Also remove `self.serpapi_client` from `__init__` since the keyword agent no longer
needs it for expansion. (It may still be injected for future use — just stop using it
in `_expand_with_free_sources`.)

**Before:**
```python
serp_queries = list(dict.fromkeys(expanded_terms))[: min(5, payload.max_keywords)]
for term in serp_queries:
    related = await self.serpapi_client.get_related_searches(term, location=self.settings.search_location)
    expanded_terms.extend(related)

return list(dict.fromkeys(term.strip() for term in expanded_terms if term.strip()))[: payload.max_keywords]
```

**After:**
```python
return list(dict.fromkeys(term.strip() for term in expanded_terms if term.strip()))[: payload.max_keywords]
```

Saves: 5 SerpAPI calls per session.

---

### Change 2 — `packages/core/src/nichefinder_core/orchestrator/graph.py`

**In `parallel_analysis_node`**, before the `asyncio.gather`, add a filter that:
1. Loads each keyword from the repository
2. Keeps only keywords with `search_intent` of `commercial` or `transactional`
3. Of those, takes the top 8 (or `MAX_SERP_ANALYSIS_KEYWORDS` from settings if present,
   else hard-code 8)
4. Falls back to first 8 discovered keywords if none have commercial/transactional intent

Add a new setting `max_serp_keywords: int = 8` to `settings.py` with alias
`MAX_SERP_KEYWORDS`.

**Before (line 57):**
```python
results = await asyncio.gather(*[analyze(keyword_id) for keyword_id in state["discovered_keyword_ids"]])
```

**After:**
```python
# Load keywords, prefer commercial/transactional intent, cap at max_serp_keywords
all_ids = state["discovered_keyword_ids"]
def intent_priority(kid: str) -> int:
    kw = services["repository"].get_keyword(kid)
    if kw and kw.search_intent and kw.search_intent.value in ("commercial", "transactional"):
        return 0
    return 1

capped_ids = sorted(all_ids, key=intent_priority)[: services["settings"].max_serp_keywords]
results = await asyncio.gather(*[analyze(keyword_id) for keyword_id in capped_ids])
```

Note: `services["settings"]` must be passed into `build_graph()`. Check how services
are wired in `workflows.py` or wherever `build_graph` is called and pass settings through.

Saves: ~42 SerpAPI calls per session (50 → 8).

---

### Change 3 — `packages/core/src/nichefinder_core/gemini/prompts.py`

**Rewrite `KEYWORD_EXPANSION_PROMPT`** to be explicit about:
- The real goal: attract Montreal clients ready to hire
- Prioritize transactional + commercial intent keywords
- Use business-owner language, not developer language
- Always include location ("Montreal", "Quebec") where natural

**Replace:**
```python
KEYWORD_EXPANSION_PROMPT = """
You are an SEO keyword research assistant for a personal technical consulting site.
Generate long-tail keyword ideas that a real person could search when looking for
services or expertise related to the seed keyword.
...
- Include both informational and commercial opportunities when they fit.
...
"""
```

**With:**
```python
KEYWORD_EXPANSION_PROMPT = """
You are an SEO keyword research assistant. Your goal is to find keywords that
Montreal small business owners and startup founders search on Google when they
are READY TO HIRE a web developer, app developer, or technical consultant.

Generate long-tail keyword variations of the seed keyword. Prioritize:
1. Transactional: "hire ...", "find ...", "... services montreal", "... developer montreal"
2. Commercial: "how much does ... cost", "best ... montreal", "... agency vs freelancer"
3. Local: include "Montreal", "Quebec", or "Canada" where natural
4. Business-owner language: write as a business owner would search, not a developer

Avoid:
- Pure informational / tutorial queries (e.g. "how to set up CI/CD")
- Developer-facing keywords (e.g. "react hooks best practices")
- Keywords without commercial or local relevance

Respond ONLY with a JSON array:
[
  {{
    "keyword": "string",
    "reasoning": "one sentence"
  }}
]
Site description: {site_description}
Target audience: {target_audience}
Services: {services}
Seed keyword: {seed_keyword}
Max keywords: {max_keywords}
""".strip()
```

**Also update `KEYWORD_INTENT_PROMPT`** — change the context line from
`"AI development, SaaS development, mobile apps, and technical consulting services"`
to reflect that the priority is local client acquisition, so `commercial` and
`transactional` intents are the target, and `informational` keywords that don't
have a local/client angle should be deprioritized.

---

### Change 4 — `packages/core/src/nichefinder_core/settings.py`

Add one new field:

```python
max_serp_keywords: int = Field(default=8, alias="MAX_SERP_KEYWORDS")
```

Place it near `serpapi_calls_per_month` (line 45).

---

## Done Criteria

- [ ] A single `seo research "web developer montreal"` run uses ≤10 SerpAPI calls (verify via usage log or Rich output)
- [ ] `keyword_agent.py` no longer calls `serpapi_client.get_related_searches()` anywhere in `_expand_with_free_sources`
- [ ] `graph.py` parallel analysis caps at 8 keywords, preferring commercial/transactional intent
- [ ] `MAX_SERP_KEYWORDS=8` is a configurable setting in `settings.py`
- [ ] `KEYWORD_EXPANSION_PROMPT` explicitly instructs Gemini to generate local commercial keywords for Montreal clients
- [ ] All existing tests pass (`uv run pytest`)
- [ ] No new test failures introduced

## Out of scope

- SERP result caching (separate stream if needed later)
- Switching away from SerpAPI to Brave or another provider
- Changes to content generation, briefing, or publishing pipeline

---

## Context for Codex

**Repo:** `/Users/danilulmashev/Documents/GitHub/ai-nichefinder`
**Branch to create:** `feature/serp-pipeline-fix` from `develop`
**Run tests with:** `uv run pytest`
**Key files:**
- `packages/core/src/nichefinder_core/agents/keyword_agent.py`
- `packages/core/src/nichefinder_core/orchestrator/graph.py`
- `packages/core/src/nichefinder_core/gemini/prompts.py`
- `packages/core/src/nichefinder_core/settings.py`

**Do not touch:**
- `packages/db/` — no schema changes needed
- `apps/cli/` — no CLI changes needed
- `data/site_config.json` — already correct
- `.env` — never commit secrets

Start by reading the 4 key files in full, then make the changes in order (1→2→3→4),
then run `uv run pytest` and fix any failures before finishing.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-20 by danilulmashev
- **What just happened:** Fixed SQLite path resolution so relative database URLs resolve from the repo root and the CLI works from subdirectories like apps/dashboard.
- **Current focus:** —
- **Next action:** Continue calibrating the free-evidence stack now that local research commands are stable regardless of current working directory.
- **Blockers:** none

## Progress log
_Append-only. Auto-trimmed by `agentboard checkpoint` to last 10 entries._

2026-04-20 11:53 — Fixed SQLite path resolution so relative database URLs resolve from the repo root and the CLI works from subdirectories like apps/dashboard.

2026-04-20 10:33 — Pre-SERP gating now layers deterministic scoring, Trends, Tavily, and DDGS before the capped SERP stage, with usage tracking for each evidence source.

2026-04-20 07:15 — Pre-SERP gate now uses deterministic scoring, Trends enrichment, and bounded Tavily validation before the capped SERP stage.

2026-04-19 22:40 — Extended pre-SERP gating with seed-fidelity and drift penalties so the capped shortlist preserves seed intent before any paid SERP validation.

2026-04-19 21:44 — Replaced the intent-only SERP shortlist with deterministic pre-SERP scoring, wired it into CLI and graph paths, added shortlist visibility, and covered duplicate and GSC-boost behavior in tests.

2026-04-19 21:13 — Removed redundant SerpAPI expansion, capped research SERP analysis at 8 keywords, refocused prompts to Montreal commercial intent, and added regression coverage.
