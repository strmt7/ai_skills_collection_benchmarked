# debug-buttercup

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/security-reference/trailofbits-skills-plugins-debug-buttercup-skills-debug-buttercup`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/security-reference/trailofbits-skills-plugins-debug-buttercup-skills-debug-buttercup/SKILL.md`

Source: [trailofbits/skills `plugins/debug-buttercup/skills/debug-buttercup/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/debug-buttercup/skills/debug-buttercup/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Debugs the Buttercup CRS (Cyber Reasoning System) running on Kubernetes. Use when diagnosing pod crashes, restart loops, Redis failures, resource pressure, disk saturation, DinD issues, or any service misbehavior in the crs namespace. Covers triage, log analysis, queue inspection, and common failure patterns for: redis, fuzzer-bot, coverage-bot, seed-gen, patcher, build-bot, scheduler, task-server, task-downloader,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-debug-buttercup-skills-debug-buttercup-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/debug-buttercup/skills/debug-buttercup/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
