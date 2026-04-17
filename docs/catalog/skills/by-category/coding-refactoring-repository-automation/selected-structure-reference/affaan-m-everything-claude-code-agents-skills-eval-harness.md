# eval-harness

Category: Coding, refactoring & repository automation

Mirrored skill: `included/skills/by-category/coding-refactoring-repository-automation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-eval-harness`

Agent-ready entrypoint: `included/agent-ready/by-category/coding-refactoring-repository-automation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-eval-harness/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/eval-harness/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/eval-harness/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Formal evaluation framework for Claude Code sessions implementing eval-driven development (EDD) principles

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-eval-harness-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/eval-harness/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `coding-refactoring-and-repository-automation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `coding-refactoring-and-repository-automation-kubernetes-examples`: Validate manifests and operational runbooks.
- `coding-refactoring-and-repository-automation-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
