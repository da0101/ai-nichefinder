---
stream_id: stream-dashboard-rework
slug: dashboard-rework
type: feature
status: in-progress
agent_owner: claude-code
domain_slugs: [viewer]
repo_ids: [repo-primary]
base_branch: develop
git_branch: feature/dashboard-rework
created_at: 2026-04-20
updated_at: 2026-04-22
closure_approved: false
---

# dashboard-rework

## Scope

- Replace the inline HTML/JS viewer with a React 18 + shadcn/ui + Tailwind app at `frontend/dashboard/`
- Add live polling (30s interval) so DB updates are visible without restarting the server
- Python server serves built `dist/` static files; all existing `/api/` routes unchanged
- Built `dist/` committed to git so `seo view` works without a node build step
- **Out of scope:** any control/action features (approve briefs, trigger workflows) — those are Phase 2

## Done criteria

- [x] `frontend/dashboard/` scaffolded with Vite + React 18 + TypeScript + Tailwind + shadcn/ui
- [x] Dashboard loads all existing data (stats bar, keyword list, keyword detail, brief, SERP pages)
- [x] Live polling: stats + sidebar refresh every 30s without page reload
- [x] `viewer_server.py` serves `dist/` static files; falls back to inline HTML if dist not built
- [x] `npm run build` produces `dist/` which works when served by the Python server
- [x] All shadcn/ui pre-delivery checklist items pass (contrast, cursors, icons, hover states)
- [x] `.platform/domains/viewer.md` updated to reflect new architecture
- [x] `.platform/memory/log.md` appended
- [x] `decisions.md` updated with React/shadcn/ui decision
- [ ] Manual verification: `seo view` opens browser, live refresh works, all sections render

## Key decisions

_Append-only. Format: `YYYY-MM-DD — <decision> — <rationale>`_

2026-04-20 — React + Vite + shadcn/ui for dashboard — Vanilla HTML/JS embedded in Python is hard to evolve; React enables live polling, future control features, and responsive layout. User explicitly requested React + shadcn/ui. npm/Node.js toolchain accepted by owner.
2026-04-20 — Built dist/ committed to git — So `seo view` works without requiring `npm install` first. Keeps the CLI local-first, no build step on end-user side.
2026-04-20 — Python server serves dist/ files — No separate web server or proxy; keeps the single-command `seo view` UX intact.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-22 by danilulmashev
- **What just happened:** Debugged profile CRUD failures, replaced stale viewer process, fixed default-vs-active runtime routing, auto-initialized per-profile DB tables, and regression-tested viewer/profile paths.
- **Current focus:** —
- **Next action:** Have the user hard-refresh the dashboard, retest create/delete/edit/switch, and then polish the profile management UX based on real interaction.
- **Blockers:** none

## Progress log

2026-04-22 22:55 — Debugged profile CRUD failures, replaced stale viewer process, fixed default-vs-active runtime routing, auto-initialized per-profile DB tables, and regression-tested viewer/profile paths.

2026-04-22 18:50 — Made business profiles production-style: SQLite-backed registry, active-profile state in DB, browser create/edit/delete dialogs, and Lucide-based profile cards. Verified backend/frontend tests and build.

2026-04-22 18:25 — Made the React dashboard usable as a scrollable workspace: separated Research Ops from Keyword Explorer, improved empty states, and validated the frontend build/tests. Also researched keyword-dashboard UX patterns and DataForSEO timing.

2026-04-22 18:08 — Expanded the React viewer into an interactive SEO testing workspace with profile switching/creation, profile config editing, training review/approval, final review, and browser-triggered validate-free via the existing Python server.

2026-04-20 — Implementation complete. React app (22 files, builds to dist/), viewer_server.py serves dist/ with inline HTML fallback, domain file updated, decision #14 recorded.
2026-04-20 11:00 — Stream bootstrapped. Design system generated (data-dense dashboard, blue/amber, Fira Code/Fira Sans). Plan proposed inline.
2026-04-21 12:10 — Added browser-open behavior to `seo view`, made selected keyword detail poll every 30s, and added HTTP-level viewer server tests. Full suite green at 93 passed.
2026-04-22 11:40 — Expanded the dashboard into an interactive testing workspace: added profile switching/creation, profile config editing, training review/approval, final-review comparison, and browser-triggered `validate-free` via new viewer server endpoints. Focused viewer/backend suites passed at `48`, Vite build green.

## Open questions

_None_

## Audit follow-up — 2026-04-21

- The two audit blockers are resolved in code: `seo view` now attempts a browser open and the selected keyword detail now refreshes on the polling cadence.
- Viewer-server regression coverage now exists for static assets, traversal rejection, and inline fallback.
- The stream is still waiting on human local verification. Frontend hook/component tests remain unbuilt because there is no existing React test harness in `frontend/dashboard`, but that is not one of this stream's formal done criteria.

---

## 🔍 Audit — 2026-04-24

> Supersedes previous audit. Run via Stream / Feature Analysis Protocol — 6 parallel/rotated agents.

# 📋 dashboard-rework — Audit Snapshot

> **Stream:** `dashboard-rework` · **Date:** 2026-04-24 · **Status:** 🟡 In progress / not ready to close
> **Repos touched:** `repo-primary`

---

## ⚡ At-a-Glance Scorecard

| | 🖥️ repo-primary |
|---|:---:|
| **Implementation** | 🟡 |
| **Tests**          | 🟡 |
| **Security**       | 🟡 |
| **Code Quality**   | 🟡 |

> **Bottom line:** The dashboard/profile workspace is substantially implemented and focused backend tests pass, but closure is blocked by missing manual verification, untracked/ignored deliverables, and local write-endpoint hardening follow-up.

---

## 🔄 How the Feature Works (End-to-End)

```text
seo view
  -> viewer command
    -> ThreadingHTTPServer
      -> GET /              -> dist/index.html or inline HTML fallback
      -> GET /assets/*      -> dist/assets/*
    -> /api/dashboard, /api/keywords/:id
    -> /api/profiles, /api/profile-config
    -> /api/training-review, /api/final-review
    -> /api/validate-free
    -> React app
      -> profile CRUD + switching
      -> training/final review
      -> validation lab
      -> keyword explorer with polling
```

---

## 🛡️ Security

| Severity | Repo | Finding |
|:---:|---|---|
| 🟢 Clean | repo-primary | Viewer defaults to loopback binding and static path traversal is guarded. [backend/apps/cli/src/nichefinder_cli/commands/viewer.py:11](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/commands/viewer.py:11), [backend/apps/cli/src/nichefinder_cli/viewer_server.py:331](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:331) |
| 🟡 Medium | repo-primary | State-changing local endpoints accept JSON without Origin/Content-Type checks. [backend/apps/cli/src/nichefinder_cli/viewer_server.py:343](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:343), [backend/apps/cli/src/nichefinder_cli/viewer_server.py:459](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:459) |
| 🟡 Medium | repo-primary | Viewer domain docs say no external API calls, but `/api/validate-free` triggers validation and records Gemini usage. [.platform/domains/viewer.md:28](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/domains/viewer.md:28), [backend/apps/cli/src/nichefinder_cli/viewer_actions.py:61](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_actions.py:61) |

---

## 🧪 Test Coverage

### repo-primary
| Area | Tested? | File |
|---|:---:|---|
| Viewer server static/fallback/traversal/browser-open | ✅ Good | [tests/test_viewer_server.py:22](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_viewer_server.py:22) |
| Viewer profile/training/action endpoints | ✅ Good | [tests/test_viewer_server.py:86](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_viewer_server.py:86) |
| Dashboard data payloads | ✅ Good | [tests/test_viewer_data.py:24](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_viewer_data.py:24) |
| CLI profile registry/runtime routing | ✅ Good | [tests/test_cli_phase1.py:349](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/tests/test_cli_phase1.py:349) |
| Frontend component rendering / interaction | 🔴 None | [frontend/dashboard/package.json:6](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/package.json:6) |
| Manual `seo view` verification recorded in stream | 🔴 None | [.platform/work/dashboard-rework.md:37](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/dashboard-rework.md:37) |
| Full regression gate | ✅ Strong | `uv run pytest -q` -> `107 passed, 1 warning`; `npm run build` -> passed |

---

## ✅ Implementation Status

### repo-primary
| Component | Status | Location |
|---|:---:|---|
| React dashboard scaffold at `frontend/dashboard/` | ✅ Done | [frontend/dashboard/src/App.tsx:10](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/src/App.tsx:10) |
| Dashboard summary polling every 30s | ✅ Done | [frontend/dashboard/src/hooks/useDashboard.ts:12](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/src/hooks/useDashboard.ts:12) |
| Keyword detail polling | ✅ Done | [frontend/dashboard/src/hooks/useKeywordDetail.ts:43](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/src/hooks/useKeywordDetail.ts:43) |
| Profile CRUD / active profile APIs | ✅ Built | [backend/apps/cli/src/nichefinder_cli/viewer_server.py:280](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:280), [backend/apps/cli/src/nichefinder_cli/viewer_actions.py:17](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_actions.py:17) |
| Python server serves built `dist/` with inline fallback | ✅ Done | [backend/apps/cli/src/nichefinder_cli/viewer_server.py:272](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:272) |
| Built `dist/` committed | ❌ Missing | [.gitignore:32](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.gitignore:32), [.platform/work/dashboard-rework.md:23](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/dashboard-rework.md:23) |
| `seo view` opens a browser window | ✅ Done | [backend/apps/cli/src/nichefinder_cli/commands/viewer.py:17](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/commands/viewer.py:17) |
| Stream closure criterion “manual verification” | ❌ Missing | [.platform/work/dashboard-rework.md:37](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/dashboard-rework.md:37) |

---

## 🔧 Open Issues

### 🔴 Must Fix (blocking)
| # | Repo | Issue |
|---|---|---|
| 1 | repo-primary | `frontend/dashboard/dist/` is ignored by `dist/`, and `git ls-files frontend/dashboard/dist` returns no tracked files, so the “built dist committed” criterion is false. [.gitignore:32](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.gitignore:32), [.platform/work/dashboard-rework.md:23](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/dashboard-rework.md:23) |
| 2 | repo-primary | Manual verification remains unchecked: `seo view` browser open, live refresh, and all sections rendering need owner/browser confirmation. [.platform/work/dashboard-rework.md:37](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/work/dashboard-rework.md:37) |
| 3 | repo-primary | Several profile/workspace implementation files are untracked, so closure/commit would omit core feature code. [backend/apps/cli/src/nichefinder_cli/viewer_actions.py:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_actions.py:1), [frontend/dashboard/src/components/ProfileConfigPanel.tsx:1](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/src/components/ProfileConfigPanel.tsx:1) |

### 🟡 Should Fix Soon
| # | Repo | Issue | Location |
|---|---|---|---|
| 1 | repo-primary | Add Origin/Content-Type protection or another local-only write guard for profile delete/save/training/validate endpoints. | [backend/apps/cli/src/nichefinder_cli/viewer_server.py:343](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:343) |
| 2 | repo-primary | Update viewer domain docs to resolve the `validate-free` external-call/spend contradiction. | [.platform/domains/viewer.md:26](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/.platform/domains/viewer.md:26) |
| 3 | repo-primary | Split oversized files before more dashboard work: `viewer_server.py`, `App.tsx`, `ProfileConfigPanel.tsx`, `runtime.py`. | [backend/apps/cli/src/nichefinder_cli/viewer_server.py:25](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/backend/apps/cli/src/nichefinder_cli/viewer_server.py:25), [frontend/dashboard/src/App.tsx:25](/Users/danilulmashev/Documents/GitHub/ai-nichefinder/frontend/dashboard/src/App.tsx:25) |

### ⚪ Known Limitations (document, not block)
| # | Limitation |
|---|---|
| 1 | React component/hook tests are still absent; current frontend confidence comes from TypeScript/build plus manual QA. |

---

## 🎯 Close Checklist / Priority Order

  □  1. 📦  Track/force-add intended dashboard `dist/` output or adjust the done criterion
  □  2. 🧾  Add/commit intended untracked source files; exclude runtime `data/profiles/*`
  □  3. 🔍  Run real browser verification for `seo view`, live refresh, create/edit/delete/switch, and section rendering
  □  4. 🛡️  Address or explicitly accept local write-endpoint hardening risk
  □  5. ✅  Get explicit owner closure approval
