# gemini-image-generation

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/creative-reference/ztj7728-gemini-image-generation`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/creative-reference/ztj7728-gemini-image-generation/SKILL.md`

Source: [ztj7728/gemini-image-generation `SKILL.md`](https://github.com/ztj7728/gemini-image-generation/blob/9d2727cab3ab9e50d20f4ba4ae57aa57755edecd/SKILL.md)

Selected ref: `default-branch HEAD`; commit `9d2727cab3ab`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Generate or edit images with Gemini using the Google GenAI SDK. Use when the user asks to create, transform, render, or save one or more images in an OpenClaw skill workflow.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-ztj7728-gemini-image-generation-skill-md`: Use the immutable source file https://github.com/ztj7728/gemini-image-generation/blob/9d2727cab3ab9e50d20f4ba4ae57aa57755edecd/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
