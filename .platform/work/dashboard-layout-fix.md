---
stream_id: stream-dashboard-layout-fix
slug: dashboard-layout-fix
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [viewer]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/serp-pipeline-fix
created_at: 2026-04-25
updated_at: 2026-04-25
closure_approved: false
---

# dashboard-layout-fix

## Scope
- Wrap the React dashboard's topbar + main content into a single rounded "global container" (GitLab-style) — visible dark stage on all four sides of the white panel.
- Round all four corners of the content panel (currently rounded only on the right).
- Keep the existing dark sidebar; add a left gap between sidebar and the content panel so the dark stage shows on the left as well.
- **Out of scope:** Sidebar visual rework, topbar feature changes, profile-management UX polish (covered by `dashboard-rework`), removing the Python viewer fallback.

## Done criteria
- [ ] `frontend/dashboard` builds (`npm run build`) with no errors after layout change.
- [ ] Visual: dark stage visible on top, right, bottom, AND left of the white content panel.
- [ ] Visual: white content panel has rounded corners on all four sides.
- [ ] Topbar lives inside the rounded panel (single unified card).
- [ ] User confirms via hard-refresh in their own browser that the layout looks like the GitLab reference.
- [ ] `.platform/memory/log.md` appended.

## Key decisions
_Append-only. Format: `YYYY-MM-DD — <decision> — <rationale>`_

2026-04-25 — Topbar moves inside the rounded panel — User wants a single GitLab-style "global container" enclosing the entire app, so topbar + main share one rounded surface instead of topbar being a separate flush bar.

## Resume state
- **Last updated:** 2026-04-25 by claude-code
- **What just happened:** Stream bootstrapped after user requested layout fix.
- **Current focus:** Modifying `AppShell.tsx` to wrap topbar + main in a single rounded panel with dark-stage padding on all four sides.
- **Next action:** Edit `AppShell.tsx`, run `npm run build`, ask user to hard-refresh.
- **Blockers:** none

## Progress log
2026-04-25 — Stream created. Layout fix scoped to `AppShell.tsx`.

## Open questions
_None_

---

## 🔍 Audit Report

_Status: not yet run_
