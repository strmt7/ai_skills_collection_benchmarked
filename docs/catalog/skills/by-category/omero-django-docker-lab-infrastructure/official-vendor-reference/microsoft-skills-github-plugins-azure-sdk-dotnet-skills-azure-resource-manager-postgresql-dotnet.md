# azure-resource-manager-postgresql-dotnet

Category: OMERO, Django, Docker & lab infrastructure

Mirrored skill: `included/skills/by-category/omero-django-docker-lab-infrastructure/official-vendor-reference/microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-postgresql-dotnet`

Agent-ready entrypoint: `included/agent-ready/by-category/omero-django-docker-lab-infrastructure/official-vendor-reference/microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-postgresql-dotnet/SKILL.md`

Source: [microsoft/skills `.github/plugins/azure-sdk-dotnet/skills/azure-resource-manager-postgresql-dotnet/SKILL.md`](https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-dotnet/skills/azure-resource-manager-postgresql-dotnet/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a2c05249c4a2`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Azure PostgreSQL Flexible Server SDK for .NET. Database management for PostgreSQL Flexible Server deployments. Use for creating servers, databases, firewall rules, configurations, backups, and high availability. Triggers: "PostgreSQL", "PostgreSqlFlexibleServer", "PostgreSQL Flexible Server", "Azure Database for PostgreSQL", "PostgreSQL database management", "PostgreSQL firewall", "PostgreSQL backup", "Postgres".

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-resource-manager-postgresql-dotnet-skill-md`: Use the immutable source file https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-dotnet/skills/azure-resource-manager-postgresql-dotnet/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `omero-django-docker-and-lab-infrastructure-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.
- `omero-django-docker-and-lab-infrastructure-ome-ngff-samples`: Read and validate multiscale microscopy data.
- `omero-django-docker-and-lab-infrastructure-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
