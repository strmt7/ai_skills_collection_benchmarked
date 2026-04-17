# twwch__comfyui-workflow-skill

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/creative-reference/twwch-comfyui-workflow-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/creative-reference/twwch-comfyui-workflow-skill/SKILL.md`

Source: [twwch/comfyui-workflow-skill `SKILL.md`](https://github.com/twwch/comfyui-workflow-skill/blob/61e6b7984de7f415a8df59c97522265cac6d3b1b/SKILL.md)

Selected ref: `default-branch HEAD`; commit `61e6b7984de7`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Use for twwch__comfyui-workflow-skill workflows. Source sections include ComfyUI Workflow Generator, Description, Activation.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-twwch-comfyui-workflow-skill-skill-md`: Use the immutable source file https://github.com/twwch/comfyui-workflow-skill/blob/61e6b7984de7f415a8df59c97522265cac6d3b1b/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
