# playwright-skill

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill/SKILL.md`

Source: [lackeyjb/playwright-skill `skills/playwright-skill/SKILL.md`](https://github.com/lackeyjb/playwright-skill/blob/289abdea7df857dc7a6ece937dbe0c5ecc964ccd/skills/playwright-skill/SKILL.md)

Selected ref: `v5.0.0`; commit `289abdea7df8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Complete browser automation with Playwright. Auto-detects dev servers, writes reusable test scripts, and supports screenshots, responsive checks, UX validation, login flows, link checks, and arbitrary browser automation. Use when the user wants to test a website, automate browser interactions, validate web functionality, or perform browser-based testing.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-lackeyjb-playwright-skill-skills-playwright-skill-skill-md`: Use the immutable source file https://github.com/lackeyjb/playwright-skill/blob/289abdea7df857dc7a6ece937dbe0c5ecc964ccd/skills/playwright-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
