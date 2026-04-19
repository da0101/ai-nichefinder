# Gotchas

_Landmines found in this codebase. Each line = one thing a fresh agent should know before touching the related area. Appended automatically during `agentboard close <slug>` harvest._

**Severity tiers** (use the emoji prefix):
- 🔴 **never-forget** — breaks prod, loses data, or wastes hours. Always surfaced in `agentboard brief`.
- 🟡 **usually-matters** — trips up most new work in the area. Surfaced when relevant domains are active.
- 🟢 **minor** — worth mentioning, not worth interrupting flow.

Format: `🔴 [domain or file] — one-line gotcha (incident date if applicable)`

---

## Entries

<!-- agentboard:gotchas:begin -->
🟡 [keyword-research] Free-source discovery can return real keywords with unknown volume/difficulty; if those are scored as zero or worst-case, the pipeline never reaches brief/article creation even though research itself works (2026-04-19).
<!-- New entries go below, newest first. Keep entries to one line each. -->
<!-- agentboard:gotchas:end -->
