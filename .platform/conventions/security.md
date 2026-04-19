# Security Conventions

Last updated: 2026-04-17

## Threat model for this repo

- Primary risk is accidental leakage of secrets, accidental overspend, or adding scraping behavior that gets the project blocked.
- There is no multi-user auth boundary yet, so local machine trust is the practical access model.

## Rules

- Never commit `.env` or paste secrets into logs, docs, tests, or generated outputs.
- Keep all paid-provider credentials behind `Settings`; do not hardcode them or pass them around as loose strings.
- Respect `robots.txt`, rate limits, and randomized delays for page scraping.
- Do not add background automation that can generate publish or request storms without explicit user approval.
- Treat generated content as untrusted until reviewed by the operator.

## What requires extra scrutiny

- New external providers
- Anything that changes publication state automatically
- Anything that touches scraping behavior or bypasses adapter-level guards
