# video-editing

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/selected-structure-reference/video-editing`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/selected-structure-reference/video-editing/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/video-editing/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/video-editing/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI-assisted video editing workflows for cutting, structuring, and augmenting real footage. Covers the full pipeline from raw capture through FFmpeg, Remotion, ElevenLabs, fal.ai, and final polish in Descript or CapCut. Use when the user wants to edit video, cut footage, create vlogs, or build video content.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-video-editing-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/video-editing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add an executable validator or helper script so the workflow has objective checks.
