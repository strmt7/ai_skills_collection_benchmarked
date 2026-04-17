# makefile-generator

Category: Coding, refactoring & repository automation

Mirrored skill: `included/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-generator`

Agent-ready entrypoint: `included/agent-ready/by-category/coding-refactoring-repository-automation/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-generator/SKILL.md`

Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/makefile-generator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-generator/SKILL.md)

Selected ref: `v1.0.0`; commit `7fe7595e4512`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Create, generate, or scaffold Makefiles with .PHONY targets and build automation.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-generator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `coding-refactoring-and-repository-automation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `coding-refactoring-and-repository-automation-kubernetes-examples`: Validate manifests and operational runbooks.
- `coding-refactoring-and-repository-automation-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Move long background material into references/ to keep SKILL.md concise.
