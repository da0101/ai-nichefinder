---
stream_id: stream-viewer-redesign
slug: viewer-redesign
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [viewer]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/viewer-redesign
created_at: 2026-04-19
updated_at: 2026-04-19
closure_approved: true
---

# viewer-redesign

## Scope

- Expose score sub-components (volume_score, difficulty_score, trend_score, intent_score, competition_score) from `OpportunityScoreRecord` in `viewer_data.py` keyword detail API
- Rewrite `viewer_server.py` HTML/CSS/JS with intuitive design for non-SEO users:
  - Plain-English metric labels and explanations
  - Color-coded score bars (green ≥70, yellow ≥50, red <50)
  - Score breakdown chart per keyword
  - Design system: blue #1E40AF primary, amber #F59E0B CTA, Fira Code/Fira Sans fonts
- Out of scope: write operations, external API calls from viewer, node build step

## Done criteria

- [x] `viewer_data.py` exposes all 5 score sub-components in keyword detail JSON
- [x] `viewer_server.py` HTML redesigned — non-SEO-friendly labels, color bars, breakdown
- [x] Design matches tokens: blue primary, amber CTA, Fira Code for code/numbers
- [x] Manual browser test: confirmed by user sign-off ("this one is ok")
- [x] No regressions in existing tests (7 passed)
- [x] `.platform/memory/log.md` appended

## Key decisions

2026-04-19 — Inline HTML in viewer_server.py — no build step, keeps viewer self-contained per project constraint

## Resume state

- **Last updated:** 2026-04-19 — claude-code
- **What just happened:** Stream registered
- **Current focus:** Update viewer_data.py, then rewrite viewer_server.py HTML
- **Next action:** Read viewer_data.py and viewer_server.py, then implement
- **Blockers:** none

## Progress log

2026-04-19 — Stream registered; design system tokens captured from ui-ux-pro-max skill

## Open questions

_None_
