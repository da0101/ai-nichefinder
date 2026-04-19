---
stream_id: stream-git-flow-setup
slug: git-flow-setup
type: feature
status: in-progress
agent_owner: codex-cli
domain_slugs: [git-workflow]
repo_ids: [repo-primary]
base_branch: develop
git_branch: chore/git-flow-setup
created_at: 2026-04-19
updated_at: 2026-04-19
closure_approved: false
---

# git-flow-setup

_Metadata rules: `stream_id` must be `stream-<slug>`, `slug` must match the filename, `status` must match `work/ACTIVE.md`, and `updated_at` should change whenever ownership or state changes._

## Scope
- Create a `develop` branch and make it the default branch for normal development.
- Preserve `main` as the release branch that only receives promoted changes from `develop`.
- Update repo and project docs so new feature work starts from `develop`.
- Push the new branch structure to GitHub and update the remote default branch.
- Out of scope: branch protection rules, CI release automation, and semantic versioning.

## Done criteria
- [ ] Local `develop` exists and is pushed to `origin`.
- [ ] GitHub default branch points to `develop`.
- [ ] Project docs state that `develop` is the integration branch, `main` is the release branch, and feature branches fork from `develop`.
- [ ] Manual verification confirms local and remote branch state.
- [ ] `.platform/memory/log.md` appended
- [ ] `decisions.md` updated if any architectural choices were made

## Key decisions
_Append-only. Format: `2026-04-19 — <decision> — <rationale>`_

2026-04-19 — Use `develop` as the default development branch and `main` as the release branch — this keeps day-to-day integration separate from release promotion while preserving a clean release line.

## Resume state
_Overwritten by `agentboard checkpoint` — the compact payload the next agent reads first. Keep this block under ~10 lines._

- **Last updated:** 2026-04-19 by codex-cli
- **What just happened:** Created and pushed `develop`, set local tracking, and updated the repo docs to use `develop` for feature work and `main` for releases.
- **Current focus:** GitHub default-branch switch
- **Next action:** Change the GitHub repo default branch from `main` to `develop` once CLI auth or manual access is available.
- **Blockers:** `gh` auth is invalid on this machine, so the GitHub default-branch setting cannot be changed programmatically yet.

## Progress log
_Append-only. `agentboard checkpoint` prepends a dated line and auto-trims to the last 10 entries. Format: `2026-04-19 HH:MM — <what happened>`._

2026-04-19 10:05 — Created `develop`, pushed it to `origin`, set local tracking, and updated repo docs to the new `develop -> feature/* -> main` flow. GitHub default-branch switch is blocked by invalid `gh` auth.

## Open questions
_Things blocked on user input. Remove when resolved._

---

## 🔍 Audit Report

> **Required:** After every audit request, paste the full standardized report here.
> Do NOT leave the audit only in chat — it must be anchored here so the next session has it.
> Format: `.platform/workflow.md` → Stream / Feature Analysis Protocol → Step 4 template.
> After a clean re-audit (all 🟢), remove this section before stream closure.

_Status: not yet run_
