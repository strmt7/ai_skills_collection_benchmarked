# makefile-validator

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator/SKILL.md`

Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/makefile-validator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-validator/SKILL.md)

Selected ref: `v1.0.0`; commit `7fe7595e4512`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Validate, lint, audit, or check Makefiles and .mk files for errors.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-makefile-validator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/makefile-validator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
