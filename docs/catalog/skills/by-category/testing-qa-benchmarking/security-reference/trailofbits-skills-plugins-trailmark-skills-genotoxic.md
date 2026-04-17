# genotoxic

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/security-reference/trailofbits-skills-plugins-trailmark-skills-genotoxic`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/security-reference/trailofbits-skills-plugins-trailmark-skills-genotoxic/SKILL.md`

Source: [trailofbits/skills `plugins/trailmark/skills/genotoxic/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/genotoxic/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Graph-informed mutation testing triage. Parses codebases with Trailmark, runs mutation testing and necessist, then uses survived mutants, unnecessary test statements, and call graph data to identify false positives, missing test coverage, and fuzzing targets. Use when triaging survived mutants, analyzing mutation testing results, identifying test gaps, finding fuzzing targets from weak tests, running mutation.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-trailmark-skills-genotoxic-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/trailmark/skills/genotoxic/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
