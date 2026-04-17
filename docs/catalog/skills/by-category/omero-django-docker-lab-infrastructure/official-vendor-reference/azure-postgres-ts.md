# azure-postgres-ts

Category: OMERO, Django, Docker & lab infrastructure

Mirrored skill: `included/skills/by-category/omero-django-docker-lab-infrastructure/official-vendor-reference/azure-postgres-ts`

Agent-ready entrypoint: `included/agent-ready/by-category/omero-django-docker-lab-infrastructure/official-vendor-reference/azure-postgres-ts/SKILL.md`

Source: [microsoft/skills `.github/plugins/azure-sdk-typescript/skills/azure-postgres-ts/SKILL.md`](https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-typescript/skills/azure-postgres-ts/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a2c05249c4a2`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Connect to Azure Database for PostgreSQL Flexible Server from Node.js/TypeScript using the pg (node-postgres) package. Use for PostgreSQL queries, connection pooling, transactions, and Microsoft Entra ID (passwordless) authentication. Triggers: "PostgreSQL", "postgres", "pg client", "node-postgres", "Azure PostgreSQL connection", "PostgreSQL TypeScript", "pg Pool", "passwordless postgres".

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-microsoft-skills-github-plugins-azure-sdk-typescript-skills-azure-postgres-ts-skill-md`: Use the immutable source file https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-typescript/skills/azure-postgres-ts/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `omero-django-docker-and-lab-infrastructure-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.
- `omero-django-docker-and-lab-infrastructure-ome-ngff-samples`: Read and validate multiscale microscopy data.
- `omero-django-docker-and-lab-infrastructure-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
