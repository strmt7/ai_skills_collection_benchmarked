# reddit-icp-monitor

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-reddit-icp-monitor`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-reddit-icp-monitor/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/reddit-icp-monitor/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/reddit-icp-monitor/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Watches subreddits for people describing the exact problem you solve, scores their relevance to your ICP, and drafts a helpful non-spammy reply for each high-signal post. Use when asked to monitor Reddit for ICP signals, find prospects on Reddit, surface pain point posts, draft helpful Reddit replies, or scan subreddits for buying signals. Trigger when a user says "monitor Reddit for my ICP", "find people on Reddit.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-reddit-icp-monitor-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/reddit-icp-monitor/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
