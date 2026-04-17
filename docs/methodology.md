# Methodology

Snapshot date: `2026-04-17`. Inputs are local checkouts of public GitHub repositories.

Rules:

1. A broad web and repository search identifies candidate public skill sources.
2. GitHub sources with a latest release use that release tag.
3. GitHub sources without releases use current default branch HEAD and record the commit SHA.
4. Only observed `SKILL.md` files count as catalog skills.
5. Adjacent `AGENTS.md`, Copilot instructions, Cursor rules, commands, hooks, and benchmark folders are context, not counted skills.
6. Every scenario-covered candidate must have at least `3` real dataset or real workflow scenarios.
7. Every cataloged skill is physically mirrored under `included/skills/` and validated against recorded SHA-256 hashes.
8. Every cataloged skill also gets a compact agent-ready entrypoint under `included/agent-ready/`.

The repository provides catalog and benchmark definitions. A skill is not marked as having passed until an external run artifact is recorded.
