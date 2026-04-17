# position-me

Category: Coding, refactoring & repository automation

Mirrored skill: `included/skills/by-category/coding-refactoring-repository-automation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-position-me`

Agent-ready entrypoint: `included/agent-ready/by-category/coding-refactoring-repository-automation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-position-me/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/position-me/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/position-me/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: A skill for position-me

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-position-me-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/position-me/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `coding-refactoring-and-repository-automation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `coding-refactoring-and-repository-automation-kubernetes-examples`: Validate manifests and operational runbooks.
- `coding-refactoring-and-repository-automation-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
