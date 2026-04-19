# Testing Conventions

Last updated: 2026-04-17

## Test stack

- `pytest`
- `pytest-asyncio`
- in-memory SQLite for repository-level tests

## Minimum bar

- Every new feature gets at least one happy-path test and one boundary or failure-path test.
- Adapter parsing and rate-limiter behavior should be tested with mocks rather than live network calls.
- Agent tests should stub external clients and assert persisted outcomes, not just returned values.
- CLI-visible workflow changes should have at least one integration-style test or a documented manual verification path.

## Current test pattern

- Repository tests create an in-memory SQLModel engine.
- Async agent tests use fake provider clients.
- Source tests mock HTTP/Playwright interactions instead of hitting the network.

## Gaps to remember

- Passing tests does not prove real provider contracts are still valid.
- Anything touching live ranking quality still needs manual validation with realistic site data.
