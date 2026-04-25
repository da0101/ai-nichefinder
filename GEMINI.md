<!-- agentboard installed 2026-04-17 -->
> **agentboard is installed** in `.platform/`. When the user says "activate this project" (or "fill in the platform pack", "run agentboard activation"), read `.platform/ACTIVATE.md` and follow its 6-step protocol. It covers scanning the project, interviewing the user, filling `.platform/`, and prepending a steady-state section to this file (without deleting any existing content).

---<!-- agentboard:root-entry:begin v=1 -->
# ai-nichefinder — Gemini CLI Entry

**What this is:** a local-first SEO research and content workflow CLI for `danilulmashev.com`. It helps a solo operator find topics worth writing, generate briefs and drafts only when the evidence supports them, and track whether published articles actually rank.

> This file applies to Claude Code, Codex CLI, and Gemini CLI equally — `AGENTS.md` and `GEMINI.md` mirror the same entry-point intent.

## Stack

Python 3.12 · `uv` workspace (3 packages) · Typer CLI · LangGraph · Pydantic v2 · SQLModel/SQLite · Rich · Ruff · pytest

## Repo Structure

Single repo — `github.com/da0101/ai-nichefinder`. Workspace members:

| Path | Role |
|---|---|
| `backend/apps/cli` | Typer entrypoint (`nichefinder` / `seo`) and command groups |
| `backend/core` | settings, models, agents, adapters, orchestration |
| `backend/db` | persistence models, repository, engine/session helpers |
| `data/` | local DB, site config, templates, cache inputs |
| `outputs/` | generated articles, reports, and audits |
| `docs/` | project notes and legacy design docs |

## How This Project Actually Works

- The CLI is the product surface for Phase 1; there is no hosted service or web UI yet.
- The workflow is local-first: settings come from `.env`, project/site inputs come from `data/site_config.json`, state lives in SQLite plus filesystem outputs.
- Keyword research, SERP analysis, briefing, drafting, approval, publishing state, ranking checks, and usage reporting already exist as local workflows.
- Gemini is the only paid service assumed enabled by default right now; every other source should stay free or free-tier unless the user opts in.
- Google-safe behavior is mandatory: no direct Google scraping, and page fetches must respect robots plus rate limits.
- Human approval stays in the loop before AI output is treated as final or published.

## Workflow

Non-trivial tasks run through the 6-stage inline workflow in `.platform/workflow.md`:
triage → interview → research → propose → execute → verify.
New non-trivial tasks must follow the new-task bootstrap (domain file → stream file → `ACTIVE.md` row → BRIEF update) before any code.

## Git Flow

- `develop` is the default development branch.
- `main` is the release branch.
- New feature branches fork from `develop`.
- Promote to `main` from `develop`, not directly from feature branches.

## Reference Pack (`.platform/`)

- `.platform/STATUS.md` — feature areas, immediate priorities, gotchas, blockers
- `.platform/architecture.md` — components, stack, data flow, invariants
- `.platform/memory/decisions.md` — locked and deferred project decisions
- `.platform/memory/log.md` — activation + session log
- `.platform/work/BRIEF.md` — active feature narrative (read every session)
- `.platform/work/ACTIVE.md` — stream registry (read every session)
- `.platform/workflow.md` — the 6-stage protocol
- `.platform/domains/` — per-domain context: `keyword-research`, `content-production`, `rank-tracking`
- `.platform/conventions/` — `python`, `cli`, `data-sources`, `security`, `testing`, `api`, `deployment`

Loading rule: only load files listed in `work/BRIEF.md` § "Relevant context". Never load `work/archive/*`. Never load `BACKLOG.md` or `learnings.md` at session start unless the task explicitly needs them.

## Hard Constraints (Don't Break These)

1. **Ranking usefulness over output volume.** If a topic has no evidence of demand or fit, generating copy for it is failure, not progress.
2. **Gemini-only paid default.** Everything else should remain free or free-tier unless the user explicitly approves more spend.
3. **CLI-first and local-first.** No hosted service, web UI, or daemon should be assumed.
4. **Google-safe acquisition only.** No raw `google.com/search` scraping or reckless page fetching.
5. **Human approval before finalization.** AI drafts are not publish-ready by default.
6. **Max ~300 lines per file.** Split instead of bloating.
7. **`.env` never committed.** Secrets stay local.

---

## Session start protocol

1. Read `.platform/work/BRIEF.md` — 30-second narrative.
2. Read `.platform/work/ACTIVE.md` — stream registry.
3. If 1 stream → confirm: "Resuming **<stream>** — next: <action>. Continue?"
4. If 2+ streams → ask which.
5. If 0 streams → ask what to work on.

If resuming an existing stream, run `agentboard handoff <slug>` before anything else.

## Mandatory Protocol — Stream Audit / Analysis

If the user asks to audit, analyze, or check the state of a stream (for example references to `work/*.md`), you must:
1. Read `.platform/workflow.md` first.
2. Follow the Stream / Feature Analysis Protocol exactly.

## Stream Closure — Human Approval Required

Only the human/owner declares a stream complete. Before archiving or removing a stream from `ACTIVE.md`:
1. Present evidence of completion.
2. Wait for explicit human sign-off.
3. Verify `closure_approved: true` in the stream file.

## Context handoff

```bash
agentboard checkpoint <stream-slug> --what "..." --next "..." \
  --cumulative-in <N> --cumulative-out <N> --provider <claude|codex|gemini> --model <model-id>
```

## Skills available (`ab-` prefix)

Claude Code loads skills from `.claude/skills/`. Codex CLI and Gemini CLI load from `.agents/skills/`. The skill set is the same:

`ab-triage`, `ab-workflow`, `ab-research`, `ab-pm`, `ab-architect`, `ab-test-writer`, `ab-security`, `ab-qa`, `ab-review`, `ab-debug`.

Read each skill's `SKILL.md` on first use.

---

_Activated 2026-04-17 and re-aligned on 2026-04-17. Content between `<!-- agentboard:root-entry:begin v=1 -->` / `<!-- agentboard:root-entry:end v=1 -->` is replaced on re-activation; everything after the end marker is preserved byte-for-byte._
<!-- agentboard:root-entry:end v=1 -->
