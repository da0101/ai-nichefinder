# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Feature:** _Git flow setup_
**Status:** blocked
**Stream file:** `work/git-flow-setup.md`

---

## What we're building

We are putting a simple Git flow in place for this repository: `develop` becomes the default branch for normal work, `main` stays the release branch, and feature branches fork from `develop`.

## Why

The repo now has enough real workflow and process state that development and release lines should be separated. This keeps integration work moving on `develop` while preserving `main` as the clean release target.

## What done looks like

- `develop` exists locally and on GitHub.
- GitHub uses `develop` as the default branch.
- New feature branches are created from `develop`.
- `main` is documented as release-only and receives promoted changes from `develop`.

## Current state

The branch topology is now in place locally and on origin, but the stream is blocked on one external GitHub setting: the repo default branch still needs to be switched from `main` to `develop`.

## Relevant context

- `.platform/STATUS.md`
- `.platform/architecture.md`
- `.platform/domains/git-workflow.md`
- `.platform/domains/keyword-research.md`
- `.platform/domains/content-production.md`
- `.platform/domains/rank-tracking.md`
- `AGENTS.md`
- `README.md`

**Never load:** `work/archive/*`
