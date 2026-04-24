# API Conventions

Last updated: 2026-04-17

## Scope

This repo consumes external HTTP APIs and now exposes a local REST control-plane API for the dashboard and automation.

## Rules

- Every outbound provider gets a dedicated adapter client in `packages/core/src/nichefinder_core/sources/` or `packages/core/src/nichefinder_core/gemini/`.
- Budget checks, rate limiting, and response parsing belong in the adapter or the domain agent, not in CLI commands.
- Commands and workflows should operate on normalized models or simple domain dicts rather than raw provider payloads.
- If a provider can incur cost, usage must be recorded or at least be easy to add to `ApiUsageRecord`.
- Exposed REST endpoints must wrap typed application actions, not arbitrary shell commands.
- Long-running REST actions should run through allowlisted jobs and return a `job_id` instead of blocking the request indefinitely.
- Mutating REST endpoints must enforce their write guard before parsing request bodies or running business logic.
- Default local write access is loopback-only; if `VIEWER_API_TOKEN` is configured, every write must present `Authorization: Bearer <token>`.

## Current adapters

- `GeminiClient`
- `SerpAPIClient`
- `TrendsClient`
- `ContentScraper`

## Anti-patterns

- Calling `httpx` directly from a command handler
- Spreading provider-specific field names across the repo
- Adding a new paid API path without a documented budget policy
- Adding a generic `/shell`, `/command`, or arbitrary task endpoint
- Leaving mutating localhost endpoints open to non-loopback callers or cross-site browser origins
