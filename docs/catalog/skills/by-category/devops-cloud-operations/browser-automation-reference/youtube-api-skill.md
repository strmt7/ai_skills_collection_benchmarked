# youtube-api-skill

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/browser-automation-reference/youtube-api-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/browser-automation-reference/youtube-api-skill/SKILL.md`

Source: [browser-act/skills `youtube-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-api-skill/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: This skill helps users automatically extract detailed video metrics and channel information from YouTube based on keyword searches using the BrowserAct API. The Agent should proactively apply this skill when users express needs such as extract specific keyword YouTube video detailed data, monitor the latest video performance of competitor channels, collect comment and like counts for videos on a specific topic,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-youtube-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
