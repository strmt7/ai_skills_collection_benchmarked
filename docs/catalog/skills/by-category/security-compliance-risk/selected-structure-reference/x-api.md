# x-api

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/selected-structure-reference/x-api`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/selected-structure-reference/x-api/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/x-api/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/x-api/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: X/Twitter API integration for posting tweets, threads, reading timelines, search, and analytics. Covers OAuth auth patterns, rate limits, and platform-native content posting. Use when the user wants to interact with X programmatically.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-x-api-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/x-api/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add an executable validator or helper script so the workflow has objective checks.
