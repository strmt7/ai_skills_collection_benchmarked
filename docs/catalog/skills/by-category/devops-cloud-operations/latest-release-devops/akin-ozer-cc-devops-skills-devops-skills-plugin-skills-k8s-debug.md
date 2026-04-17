# k8s-debug

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-debug`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/latest-release-devops/akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-debug/SKILL.md`

Source: [akin-ozer/cc-devops-skills `devops-skills-plugin/skills/k8s-debug/SKILL.md`](https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-debug/SKILL.md)

Selected ref: `v1.0.0`; commit `7fe7595e4512`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Diagnose and fix Kubernetes pods, CrashLoopBackOff, Pending, DNS, networking, storage, and rollout failures with kubectl.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-akin-ozer-cc-devops-skills-devops-skills-plugin-skills-k8s-debug-skill-md`: Use the immutable source file https://github.com/akin-ozer/cc-devops-skills/blob/7fe7595e4512f8ce43dcf956aa5190b96d627dd1/devops-skills-plugin/skills/k8s-debug/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
