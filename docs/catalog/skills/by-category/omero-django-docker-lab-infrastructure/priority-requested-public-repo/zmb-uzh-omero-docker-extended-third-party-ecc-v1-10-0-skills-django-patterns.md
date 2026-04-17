# django-patterns

Category: OMERO, Django, Docker & lab infrastructure

Mirrored skill: `included/skills/by-category/omero-django-docker-lab-infrastructure/priority-requested-public-repo/zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-patterns`

Agent-ready entrypoint: `included/agent-ready/by-category/omero-django-docker-lab-infrastructure/priority-requested-public-repo/zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-patterns/SKILL.md`

Source: [ZMB-UZH/omero-docker-extended `third_party/ecc-v1.10.0/skills/django-patterns/SKILL.md`](https://github.com/ZMB-UZH/omero-docker-extended/blob/b7c7cfa2a057f08eb872aadae49d89f521480114/third_party/ecc-v1.10.0/skills/django-patterns/SKILL.md)

Selected ref: `default-branch HEAD`; commit `b7c7cfa2a057`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Django architecture patterns, REST API design with DRF, ORM best practices, caching, signals, middleware, and production-grade Django apps.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-zmb-uzh-omero-docker-extended-third-party-ecc-v1-10-0-skills-django-patterns-skill-md`: Use the immutable source file https://github.com/ZMB-UZH/omero-docker-extended/blob/b7c7cfa2a057f08eb872aadae49d89f521480114/third_party/ecc-v1.10.0/skills/django-patterns/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `omero-django-docker-and-lab-infrastructure-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.
- `omero-django-docker-and-lab-infrastructure-ome-ngff-samples`: Read and validate multiscale microscopy data.
- `omero-django-docker-and-lab-infrastructure-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Move long background material into references/ to keep SKILL.md concise.
