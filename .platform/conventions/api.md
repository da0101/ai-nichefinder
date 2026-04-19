# API Conventions

Last updated: 2026-04-17

## Scope

This repo consumes external HTTP APIs rather than exposing its own public API.

## Rules

- Every outbound provider gets a dedicated adapter client in `packages/core/src/nichefinder_core/sources/` or `packages/core/src/nichefinder_core/gemini/`.
- Budget checks, rate limiting, and response parsing belong in the adapter or the domain agent, not in CLI commands.
- Commands and workflows should operate on normalized models or simple domain dicts rather than raw provider payloads.
- If a provider can incur cost, usage must be recorded or at least be easy to add to `ApiUsageRecord`.

## Current adapters

- `GeminiClient`
- `SerpAPIClient`
- `TrendsClient`
- `ContentScraper`

## Anti-patterns

- Calling `httpx` directly from a command handler
- Spreading provider-specific field names across the repo
- Adding a new paid API path without a documented budget policy
