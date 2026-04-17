# hackernews-intel

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-hackernews-intel`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-hackernews-intel/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/hackernews-intel/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/hackernews-intel/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Monitors Hacker News for user-configured keywords, deduplicates against a local SQLite cache, and sends Slack alerts for new matching posts. Use when asked to monitor Hacker News for mentions, track keywords on HN, get alerts when something is posted about a topic on Hacker News, or set up HN keyword monitoring. Trigger when a user mentions Hacker News alerts, HN monitoring, keyword tracking on HN, or wants to know.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-hackernews-intel-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/hackernews-intel/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
