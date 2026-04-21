---
stream_id: stream-reddit-api-integration
slug: reddit-api-integration
type: feature
status: blocked
agent_owner: codex
domain_slugs: [keyword-research]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/reddit-api-integration
created_at: 2026-04-21
updated_at: 2026-04-21
closure_approved: false
---

# reddit-api-integration

## Scope
- Add Reddit as an official read-only enrichment source for buyer-problem and article-brief research.
- Use the approved Reddit Data API path with OAuth and a descriptive User-Agent; do not rely on raw HTML scraping.
- Keep Reddit as a supporting evidence source for repeated pain points, language patterns, and question discovery rather than a primary ranking validator.
- Fit the integration into the existing local-first CLI workflow with cache-aware, rate-limited retrieval and small structured outputs.
- Out of scope: posting, commenting, voting, moderation actions, Devvit app work, or model training on Reddit data.

## Done criteria
- [ ] Reddit API access is approved and the required credentials are available locally.
- [ ] A read-only Reddit source module can fetch public posts/comments relevant to shortlisted topics.
- [ ] Reddit outputs are summarized into structured buyer-signal/question/phrase evidence suitable for the brief pipeline.
- [ ] Tests pass for the Reddit source and integration path.
- [ ] Manual verification shows Reddit-derived evidence improving brief quality without polluting keyword validation.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
2026-04-21 — Treat Reddit as a read-only enrichment source, not a primary keyword validator — forum discussion quality is valuable for pain-point discovery but should not override SERP evidence.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-21 by codex
- **What just happened:** Submitted Reddit API access request for an external non-Devvit local research tool use case.
- **Current focus:** Wait for Reddit approval while keeping the integration explicitly tracked.
- **Next action:** When Reddit responds, wire credentials into local settings and implement a read-only Reddit source module plus brief-enrichment outputs.
- **Blockers:** Waiting for Reddit Data API approval response.

## Progress log
2026-04-21 11:00 — Created the stream after submitting a Reddit Data API access request for ai-nichefinder's external read-only research workflow.

## Open questions
- Which subreddits should be included in the initial allowlist for business/SEO/web-development topic enrichment?
- How much raw Reddit text, if any, should be cached locally versus summarized immediately into structured evidence?

---

## 🔍 Audit Report

_Status: not yet run_
