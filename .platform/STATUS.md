# ai-nichefinder — Current Status

Last updated: 2026-04-19

> Local-first CLI for researching SEO opportunities, generating rank-aware content briefs and drafts, and tracking whether articles for `danilulmashev.com` actually earn search visibility.

---

## Feature areas

| Area | Status | Last touched | Notes |
|---|---|---|---|
| Keyword research + opportunity scoring | ✓ Done | 2026-04-19 | Research stores keywords in SQLite, applies deterministic scoring, and uses neutral fallbacks when free-source metrics are unknown. |
| SERP + competitor analysis | ✓ Done | 2026-04-19 | SerpAPI, trend analysis, and robots-respecting competitor scraping run end to end; scrape failures now skip instead of aborting the brief flow. |
| Content briefs + article generation | ✓ Done | 2026-04-19 | Brief generation, draft creation, rewrite flow, approval gating, and markdown outputs were live-validated on a real discovered keyword. |
| Rank tracking + reporting | ✓ Done | 2026-04-19 | Ranking snapshots, reports, budget visibility, keyword inspection, and the lightweight local viewer are available for Phase 1 local operations. |
| Platform context + workflow docs | ✓ Done | 2026-04-19 | Phase 1 scope, audit evidence, and operator-facing docs now match the actual local product shape. |

**Legend:**
- ✓ Done — shipped, tested, merged
- 🔵 Exists — in place but may need review
- ⧗ Pending — planned, not started
- ⚠ Flagged — known issue that needs attention
- 🔴 Deferred — decided to punt (reference `decisions.md` entry)

## Immediate priorities

1. **Add first-party monitoring** — integrate Google Search Console first, then GA4, so the workflow can learn from impressions, clicks, CTR, and average position instead of only pre-publish heuristics.
2. **Deepen the measurement loop** — improve rank and performance reporting so the system can recommend refresh vs new article using live site evidence.
3. **Promote orchestration deliberately** — move from direct CLI workflow calls toward the intended multi-agent runtime only after the data-collection layer is stronger.

## Open decisions

| # | Question | Deadline |
|---|---|---|
| 1 | When should OpenAI be added alongside Gemini, and which workflows justify the extra spend? | Before Phase 2 model expansion |
| 2 | Should LinkedIn profile optimization live in this repo or in a separate personal-brand workflow? | Before building any LinkedIn automation |
| 3 | Which follow-on stream should start next: `gsc-monitoring`, `data-model-v2`, or a combined monitoring-foundation stream? | Before the next major implementation stream |

## Release blocklist

Things that must be resolved before this project ships / goes live:

- [ ] Add first-party performance imports before relying on the platform for iterative SEO optimization.
- [ ] Decide the next monitoring-focused stream and lock its scope before widening the architecture.
- [ ] Keep source-policy discipline intact as new providers are added.

## Known gotchas (pinned)

Things that will bite every new session if not flagged upfront.

- **Activation drift happened once already** — older root docs described a different product shape; always trust the current code and `.platform/` over stale session memory.
- **Tests are mostly mocked and local** — the Phase 1 loop is live-verified, but deeper confidence still requires first-party integrations such as Search Console.
- **External-source assumptions need periodic review** — if a provider is not part of the approved workload, remove it from code and docs instead of leaving it as dormant complexity.
- **Playwright scraping is allowed only with robots/rate-limit discipline** — do not add shortcuts that fetch pages faster or more aggressively than the current guards.

## File size violations

> Global rule: max ~300 lines per file. Track known offenders here so they get split before being added to.

- `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` are intentionally long entry files because they carry agentboard markers plus preserved activation context.

---

_For per-layer status (if this is a multi-repo / multi-layer project), see STATUS-{layer}.md files alongside this one._
