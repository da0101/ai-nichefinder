---
domain_id: dom-git-workflow
slug: git-workflow
status: active
repo_ids: [repo-primary]
related_domain_slugs: []
created_at: 2026-04-19
updated_at: 2026-04-19
---

# git-workflow

_Metadata rules: `domain_id` must be `dom-<slug>`, `slug` must match the filename, `repo_ids` should name the repos this domain touches, and `updated_at` should change whenever contracts or touch-points change._

## What this domain does

Defines how code moves through branches in this repository so everyday development, release preparation, and feature isolation follow one predictable path. The outcome is simple: feature work starts from `develop`, releases promote into `main`, and the branch strategy is documented in the same place the rest of the platform context lives.

## Backend / source of truth

- Git branch topology in the local repository and on GitHub is the source of truth.
- The repo's default branch and merge target rules are part of this domain.
- `.platform/` stream metadata must reflect the real base branch used for new work.

## Frontend / clients

- GitHub branch selection for PRs and feature branches.
- Local developer workflows when starting a new stream or feature branch.
- Project documentation that tells future agents and humans which branch to branch from and which branch releases from.

## API contract locked

- `develop` is the default development branch.
- `main` is the release branch.
- New feature branches fork from `develop`, not `main`.
- `main` only receives changes promoted from `develop`.

## Key files

- `.platform/domains/git-workflow.md`
- `.platform/STATUS.md`
- `.platform/work/ACTIVE.md`
- `.platform/work/BRIEF.md`
- `README.md`
- `AGENTS.md`

## Decisions locked

- `develop` is the integration branch for normal work.
- `main` is reserved for release-ready code.
- New streams and feature branches should use `develop` as their base unless an explicit exception is recorded.
- Branch policy should be documented in project context, not left as tribal knowledge.
