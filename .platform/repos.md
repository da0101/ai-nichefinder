# ai-nichefinder — Repos & Specialist Routing

Last updated: 2026-04-17

---

## Repos

| Repo ID | Path | Role / stack hint | Deep reference |
|---|---|---|---|
| repo-primary | `.` | Python workspace / Typer CLI / SQLModel / LangGraph | `architecture.md` |

For single-repo projects, this file just has one row.

## Conventions — which file governs which area

| Area you're touching | Read first |
|---|---|
| HTTP / API clients | `conventions/api.md` |
| Auth / secrets / scraping safety | `conventions/security.md` |
| Tests | `conventions/testing.md` |
| Deploy / release / rollback | `conventions/deployment.md` |
| CLI behavior and command design | `conventions/cli.md` |
| Source adapters / rate limits / budgets | `conventions/data-sources.md` |
| Stack-specific rules | `conventions/python.md` |

## Specialist routing (if you use Claude Code skills)

| When you touch... | Use skill |
|---|---|
| Project triage or scoping | `ab-triage` |
| Medium+ workflow orchestration | `ab-workflow` |
| Python/domain architecture | `ab-architect` |
| Test coverage work | `ab-test-writer` |
| Bug investigation | `ab-debug` |
| Security or source-safety review | `ab-security` |
| Pre-merge code review | `ab-review` |

## Hard repo rules carried over from the platform

These apply to every repo in this project:

1. Max ~300 lines per file
2. No secrets in code, logs, or committed files
3. Only Google-safe acquisition techniques are allowed
4. External calls must flow through the adapter clients in `conventions/api.md`
5. Every new feature has at least one happy-path + one edge-case test
