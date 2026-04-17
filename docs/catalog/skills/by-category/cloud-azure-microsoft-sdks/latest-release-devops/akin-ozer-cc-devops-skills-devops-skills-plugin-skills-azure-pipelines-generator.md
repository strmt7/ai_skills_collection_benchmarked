# azure-pipelines-generator

Category: Cloud, Azure & Microsoft SDKs

Mirrored skill: `included/skills/by-category/cloud-azure-microsoft-sdks/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator`

Agent-ready entrypoint: `included/agent-ready/by-category/cloud-azure-microsoft-sdks/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator/SKILL.md`

Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/azure-pipelines-generator/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/azure-pipelines-generator/SKILL.md)

Selected ref: `v1.0.0`; commit `7fe7595e4512`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Generate/create/scaffold azure-pipelines.yml, stages, jobs, steps, or reusable templates.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-azure-pipelines-generator-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/azure-pipelines-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `cloud-azure-and-microsoft-sdks-kubernetes-examples`: Validate manifests and operational runbooks.
- `cloud-azure-and-microsoft-sdks-opentelemetry-demo`: Debug telemetry across microservices.
- `cloud-azure-and-microsoft-sdks-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
