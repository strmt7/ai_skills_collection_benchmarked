# llms-txt-generator

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/llms-txt-generator/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/llms-txt-generator/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Generates and maintains a standards-compliant llms.txt file for any website — either by crawling the live site OR by reading the website's codebase directly. Use this skill when asked to create an llms.txt, add AI discoverability to a site, improve GEO (Generative Engine Optimization), make a website readable by AI agents, generate an llms-full.txt, check if a site has llms.txt, or audit a site's AI readiness for.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-llms-txt-generator-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/llms-txt-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
