# Platform Learnings — Bug Post-Mortems & Hard-Won Patterns

> **When to write here:** after fixing a non-obvious bug (one that took >10 min to diagnose OR required reading unfamiliar internals). Append immediately in Stage 6.
> **When to read here:** before diagnosing any non-obvious bug — grep this file first by symptom keyword. Don't re-diagnose a known class of problem.
> **Never auto-loaded** at session start. Load only when investigating a bug or appending a new entry.

Format:

```
## L-NNN — <short title>
Date: YYYY-MM-DD | Repo: <repo>
Symptom: <what the user/developer sees>
Root cause: <the actual reason>
Fix: <what was changed and where>
Class: <the category of problem — so you can grep it>
```

---

## L-001 — Free-source keywords can stall the artifact path
Date: 2026-04-19 | Repo: repo-primary
Symptom: Live research completed and stored keywords, but `brief` never produced a brief for discovered topics even after the external providers were working.
Root cause: The opportunity gate treated missing volume and difficulty on free-source (`gemini_serpapi`) keywords as effectively worst-case values, so real discovered keywords never crossed the score threshold needed for brief and draft creation.
Fix: Added neutral fallback scoring in `packages/core/src/nichefinder_core/settings.py` and `packages/core/src/nichefinder_core/agents/synthesis_agent.py`, then validated the fix with a real `brief` and `write` run.
Class: scoring / workflow-threshold / live-validation

<!-- Append new entries above this line, newest at top. -->
<!-- Use sequential IDs: L-001, L-002, … -->
