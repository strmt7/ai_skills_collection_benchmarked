# webapp-testing

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/official-reference/webapp-testing`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/official-reference/webapp-testing/SKILL.md`

Source: [anthropics/skills `skills/webapp-testing/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/webapp-testing/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-webapp-testing-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/webapp-testing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
