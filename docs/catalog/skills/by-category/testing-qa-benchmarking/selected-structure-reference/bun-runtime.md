# bun-runtime

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/bun-runtime/SKILL.md`](https://github.com/affaan-m/ECC/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/bun-runtime/SKILL.md)

Selected ref: `v2.2.3`; commit `c05b2d6614f6`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Bun as runtime, package manager, bundler, and test runner. When to choose Bun vs Node, migration notes, and Vercel support.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-bun-runtime-skill-md`: Use the immutable source file https://github.com/affaan-m/ECC/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/bun-runtime/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add an executable validator or helper script so the workflow has objective checks.
