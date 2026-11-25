# coding-standards

Category: Frontend, UI & browser automation

Mirrored skill: `included/skills/by-category/frontend-ui-browser-automation/selected-structure-reference/coding-standards`

Agent-ready entrypoint: `included/agent-ready/by-category/frontend-ui-browser-automation/selected-structure-reference/coding-standards/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/coding-standards/SKILL.md`](https://github.com/affaan-m/ECC/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/coding-standards/SKILL.md)

Selected ref: `v2.2.3`; commit `c05b2d6614f6`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Baseline cross-project coding conventions for naming, readability, immutability, and code-quality review. Use detailed frontend or backend skills for framework-specific patterns. Use when reviewing code quality or naming with no framework-specific skill that applies.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-coding-standards-skill-md`: Use the immutable source file https://github.com/affaan-m/ECC/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/coding-standards/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `frontend-ui-and-browser-automation-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `frontend-ui-and-browser-automation-coco-captions`: Evaluate image understanding and visual QA tasks.
- `frontend-ui-and-browser-automation-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Move long background material into references/ to keep SKILL.md concise.
