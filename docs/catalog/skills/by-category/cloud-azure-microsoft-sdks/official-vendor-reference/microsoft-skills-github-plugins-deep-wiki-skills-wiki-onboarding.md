# wiki-onboarding

Category: Cloud, Azure & Microsoft SDKs

Mirrored skill: `included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/microsoft-skills-github-plugins-deep-wiki-skills-wiki-onboarding`

Agent-ready entrypoint: `included/agent-ready/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/microsoft-skills-github-plugins-deep-wiki-skills-wiki-onboarding/SKILL.md`

Source: [microsoft/skills `.github/plugins/deep-wiki/skills/wiki-onboarding/SKILL.md`](https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/deep-wiki/skills/wiki-onboarding/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a2c05249c4a2`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Generates four audience-tailored onboarding guides in an onboarding/ folder — Contributor, Staff Engineer, Executive, and Product Manager. Use when the user wants onboarding documentation for a codebase.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-microsoft-skills-github-plugins-deep-wiki-skills-wiki-onboarding-skill-md`: Use the immutable source file https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/deep-wiki/skills/wiki-onboarding/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `cloud-azure-and-microsoft-sdks-kubernetes-examples`: Validate manifests and operational runbooks.
- `cloud-azure-and-microsoft-sdks-opentelemetry-demo`: Debug telemetry across microservices.
- `cloud-azure-and-microsoft-sdks-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
