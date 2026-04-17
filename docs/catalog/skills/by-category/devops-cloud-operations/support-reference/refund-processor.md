# refund-processor

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/support-reference/refund-processor`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/support-reference/refund-processor/SKILL.md`

Source: [composio-community/support-skills `refund-processor/SKILL.md`](https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/refund-processor/SKILL.md)

Selected ref: `default-branch HEAD`; commit `b4f842c3cbdc`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Process a refund request by gathering context and preparing the refund workflow.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-composio-community-support-skills-refund-processor-skill-md`: Use the immutable source file https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/refund-processor/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
