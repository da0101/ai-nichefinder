# Session Log

One line per completed task. Newest at the top. Append-only.

Format: `YYYY-MM-DD — <task> — <outcome> — <takeaway>`

2026-04-22 — dashboard interactive testing workspace — extended the React viewer into a browser-driven SEO testing surface with profile management, config editing, training approval, final review, and validate-free actions; viewer/backend tests green at 48 and Vite build green — once profile-scoped SEO workflows exist, the browser must drive them directly or the CLI remains the bottleneck

2026-04-21 — multi-business training isolation — added profile-scoped runtime state, hard reset command, positive/negative training memory, and cross-profile final review; focused pytest suites green at 43 passed — training is only trustworthy when each business learns in its own sandbox and the operator can inspect the final summary before trusting it

2026-04-21 — buyer-problem learned-noise memory — added site-scoped observation capture, review/approval CLI, and soft memory-aware demotions; focused pytest suites green at 27 + 12 passed — repeated validation runs are useful only if learning stays reviewable and per-site instead of auto-blacklisting globally

2026-04-21 — cross-stream audit cleanup — closed the audited code gaps around free-validation recurrence, source health, GSC CLI coverage, viewer refresh/open behavior, and SERP shortlist caps; full pytest green at 93 passed — audit snapshots need fast reconciliation or they become stale faster than the code

2026-04-20 — DDGS evidence layer before SERP — added bounded DDGS cross-checking on top of deterministic scoring, Trends, and Tavily; full pytest green at 61/61 — free research sources help only when their weight stays below seed fidelity and drift controls

2026-04-20 — dashboard-rework — React 18 + shadcn/ui dashboard built and served by Python; live 30s polling eliminates server restart requirement — inline HTML in Python strings doesn't scale; dist/ committed to git keeps CLI-first UX intact

---
- 2026-04-24 — commit `318a1f9`: update — auto-logged
- 2026-04-21 — commit `d8adaff`: chore: absorb log auto-update — auto-logged
- 2026-04-21 — commit `41ec9e8`: feat: harden free validation and track API integrations — auto-logged
- 2026-04-20 — commit `61eb5c1`: updated engins — auto-logged
- 2026-04-19 — buyer-problem-first discovery v0 — structured buyer problems now precede keyword expansion and the no-SERP shortlist shifted toward cost/timeline/comparison terms — smart keyword systems need a problem artifact, not just better scoring on raw keyword lists
- 2026-04-19 — commit `da66d4b`: Close viewer-redesign stream: archive, remove from ACTIVE.md — auto-logged
- 2026-04-19 — commit `08c430a`: chore: absorb log auto-update — auto-logged
- 2026-04-19 — commit `6757ed4`: chore: absorb platform hook auto-updates — auto-logged
- 2026-04-19 — commit `72bb6c5`: Add --force to write/brief commands and SerpAPI usage counter — auto-logged
- 2026-04-19 — viewer-redesign — score breakdown + plain-English labels + blue/amber design system shipped — non-SEO users can now read scores without knowing jargon
- 2026-04-19 — commit `b049ad1`: feat: Rich spinner on every waiting step during seo research — auto-logged
- 2026-04-19 — commit `c217749`: fix: pytrends 429 graceful fallback, remove score cap, informational seeds — auto-logged
- 2026-04-19 — commit `7a80d71`: feat: real-time console feedback during seo research pipeline — auto-logged
- 2026-04-19 — commit `505ff0f`: feat: Montreal-focused SEO targeting — location wired end-to-end, seeds updated — auto-logged
- 2026-04-19 — commit `1abddc4`: docs: add CLI cheat sheet — auto-logged
- 2026-04-19 — commit `a9a9c92`: feat(db): auto-backup before init, backup/export commands, WAL mode — auto-logged
- 2026-04-19 — commit `72f6544`: feat(gsc-monitoring): GSC adapter, upsert, monitor sync CLI (53 tests pass) — auto-logged
- 2026-04-19 — commit `a396ce1`: Register gsc-monitoring stream: domain file, stream file, ACTIVE.md, BRIEF.md — auto-logged
- 2026-04-19 — commit `05585cb`: Close data-model-v2 stream: archive, clear ACTIVE.md, reset BRIEF.md, log closure — auto-logged
2026-04-19 — stream data-model-v2 closed — V2 schema, scoring signals, monitoring contracts merged to develop (48 tests) — additive migrations + deterministic scoring are the right pattern for schema evolution without breaking Phase 1 flows
- 2026-04-19 — commit `e6c170f`: chore: absorb agentboard hook auto-updates — auto-logged
- 2026-04-19 — commit `a72fee6`: Fix audit findings: consolidate migration, add provenance + freshness tests (48 pass) — auto-logged
- 2026-04-19 — commit `0478aa5`: chore: absorb agentboard hook auto-updates — auto-logged
- 2026-04-19 — commit `949a5bb`: chore: absorb agentboard hook auto-updates — auto-logged
- 2026-04-19 — commit `8479d09`: Update stream file and log after agentboard auto-update — auto-logged
- 2026-04-19 — commit `0cee149`: update — auto-logged
- 2026-04-19 — commit `e8342a1`: update — auto-logged
- 2026-04-19 — commit `e1e6613`: Data Model V2: scoring signals, monitoring contracts, and provenance — auto-logged
- 2026-04-19 — commit `926d5f7`: Archive git flow setup stream — auto-logged

2026-04-19 — closed stream git-flow-setup → ./.platform/work/archive/git-flow-setup.md (by danilulmashev)
2026-04-19 — closed stream repo-cleanup → ./.platform/work/archive/repo-cleanup.md (by codex-cli)
2026-04-19 — Data Model V2 slice 1 — added additive keyword metadata, score-history persistence, and SQLite upgrade support; all existing tests still pass
2026-04-19 — repo cleanup pass — removed stale architecture/docs artifacts, dead docker scaffolding, duplicate env templates, and local junk so the tracked surface matches the current CLI-first workflow
- 2026-04-19 — commit `959b2dc`: Mark git flow setup blocked on GitHub default branch — auto-logged
- 2026-04-19 — commit `d047bb3`: Set develop-based git flow — auto-logged
- 2026-04-19 — commit `f3ea03d`: Record Phase 1 closure log — auto-logged
- 2026-04-19 — commit `d434080`: Complete Phase 1 SEO CLI foundation — auto-logged

2026-04-19 — closed stream phase-1-foundation → ./.platform/work/archive/phase-1-foundation.md (by danilulmashev)

2026-04-19 — Live Phase 1 verification uncovered scoreability gap — real research now works on Gemini 2.5 and SerpAPI, but free-source keywords still lack volume/difficulty so briefs are never created — a workflow is not "done" until its live data path reaches the artifact-creation threshold
2026-04-19 — Phase 1 closure audit — re-audited the stream and found the remaining blockers are live env setup and missing real manual workflow evidence — closure should be blocked by real operator readiness, not guessed from tests alone
2026-04-18 — Robots fail-closed + CLI coverage — robots retrieval errors now deny scraping by default and CLI tests cover `research` plus `report` — source-safety rules need explicit defaults and command-level verification
2026-04-18 — Phase 1 scoping contract — narrowed the stream to the current local CLI workflow and separated it from the larger 6-agent roadmap — streams need hard closure boundaries or they absorb future architecture indefinitely
2026-04-18 — DataForSEO removal — removed the provider from runtime, config, docs, and tests — unsupported providers should be deleted, not left dormant
2026-04-18 — Publish guard enforcement — draft articles can no longer be published directly — human review rules need command-level enforcement, not just process docs
2026-04-18 — Keyword discovery fallback — default research path now works without DataForSEO — paid-source assumptions must be enforced in code, not just in docs
2026-04-17 — Re-activated project context — `.platform/` and root entry files now match the current local SEO CLI — future sessions should trust repo reality over stale activation assumptions
2026-04-17 — Initialized project with agentboard — created .platform/ context pack — workflow, conventions, and templates are in place; next task is to fill STATUS.md and architecture.md
2026-04-20 — Free multi-engine research buckets — added bounded Bing and Yahoo research adapters alongside DDGS, grouped validation output by source, and extended `seo validate-free` to scrape engine-backed articles into separate keyword-bank evidence buckets before Tavily/SerpAPI

2026-04-20 — debug: Bing validation always returned no evidence — fixed root cause: Bing HTML SERP was serving a challenge page, so the adapter now uses the RSS feed with XML parsing and keeps empty-result HTML snapshots for inspection
2026-04-22 — debug: dashboard profile CRUD instability — fixed root cause: the browser was hitting a stale viewer server, and the current viewer also mis-routed default profile runtime reads through the active profile while failing on empty profile DBs — local viewer debugging needs both process freshness checks and explicit default-vs-active runtime tests
2026-04-24 — debug: profile delete resurrection — fixed root cause: bootstrap reimported leftover profile directories after deletion — deleted profiles now remove site_config marker and bootstrap ignores partial profile dirs
2026-04-24 — rest-api-control-plane — added typed local REST status/jobs API with allowlisted validate-free job and shell-action rejection — future cloud API must wrap app actions, not commands
2026-04-24 — rest-api-control-plane — added allowlisted research jobs through REST without shell execution — API can now launch validation and research workflows by job id
2026-04-24 — rest-api-control-plane — persisted REST job state in SQLite and added restart-survival coverage — job ids can now be inspected after local server restart instead of disappearing with process memory
2026-04-24 — rest-api-control-plane — added token-or-loopback write guards for mutating endpoints and denial-path coverage — localhost stays usable by default while configured token mode protects cloud-style deployments from open write access
2026-04-24 — rest-api-control-plane — added allowlisted brief and write jobs with persisted results — content generation can now run through the REST job layer instead of only through the CLI
2026-04-24 — rest-api-control-plane — added articles/report/budget endpoints plus article approve/publish mutations and settings-aware direct actions — the API now covers more of the non-interactive CLI surface with real DB-backed tests
