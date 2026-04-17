# docs-from-code

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-docs-from-code`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-docs-from-code/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/docs-from-code/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/docs-from-code/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Generates and updates README.md and API reference docs by reading your codebase's functions, routes, types, schemas, and architecture. Uses graphify to build a knowledge graph first, then writes accurate docs from it. Use when asked to write docs, generate a README, document an API, update stale docs, create an API reference from code, add an architecture section, or document a project in any language. Trigger when.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-docs-from-code-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/docs-from-code/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
