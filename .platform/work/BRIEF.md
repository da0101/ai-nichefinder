# Feature Brief — ai-nichefinder

> Read this first — every session, every agent (Claude, Codex, Gemini).
> 30-second orientation: what we're building, why, and where we stand.

**Feature:** _Repo Cleanup_
**Status:** awaiting-verification
**Stream file:** `work/repo-cleanup.md`

---

## What we're building

We are doing a major repo hygiene pass so the working tree, docs, config surface, and ignored artifacts match the actual product. The goal is to remove dead files, duplicate templates, and local junk before continuing Phase 2 implementation.

## Why

The repo has accumulated stale architecture/docs files, duplicate env templates, dead docker scaffolding, and generated local artifacts. Leaving that in place increases confusion and makes Phase 2 work riskier because the tracked surface no longer cleanly reflects the real system.

## What done looks like

- Stale tracked files and duplicate templates are removed or consolidated.
- Untracked local junk and generated artifacts are cleared from the working tree.
- `.platform` accurately shows cleanup as the active stream during this pass.
- The remaining repo surface matches the actual CLI-first, local-first workflow.

## Current state

Phase 1 is complete, and Data Model V2 remains the next roadmap feature stream. Before resuming that work, this cleanup stream is removing stale files and unused scaffolding so Phase 2 continues on a tighter repo surface.

## Relevant context

- `.platform/STATUS.md`
- `.platform/architecture.md`
- `.platform/domains/repo-hygiene.md`
- `.platform/work/repo-cleanup.md`
- `.gitignore`
- `README.md`

**Never load:** `work/archive/*`
