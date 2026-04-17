# designing-workflow-skills

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/security-reference/designing-workflow-skills`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/security-reference/designing-workflow-skills/SKILL.md`

Source: [trailofbits/skills `plugins/workflow-skill-design/skills/designing-workflow-skills/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/workflow-skill-design/skills/designing-workflow-skills/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Guides the design and structuring of workflow-based Claude Code skills with multi-step phases, decision trees, explicit workflow routing, and progressive disclosure. Use when creating skills that involve sequential pipelines, routing patterns, safety gates, task tracking, phased execution, or any multi-step workflow. Also applies when reviewing or refactoring existing workflow skills for quality.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-workflow-skill-design-skills-designing-workflow-skills-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/workflow-skill-design/skills/designing-workflow-skills/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
