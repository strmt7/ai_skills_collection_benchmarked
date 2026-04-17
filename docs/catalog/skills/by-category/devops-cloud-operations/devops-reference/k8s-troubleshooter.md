# k8s-troubleshooter

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/devops-reference/k8s-troubleshooter`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/devops-reference/k8s-troubleshooter/SKILL.md`

Source: [ahmedasmar/devops-claude-skills `k8s-troubleshooter/skills/SKILL.md`](https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/k8s-troubleshooter/skills/SKILL.md)

Selected ref: `default-branch HEAD`; commit `1489c33ad882`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Systematic Kubernetes troubleshooting and incident response. Use this skill whenever the user mentions Kubernetes, K8s, kubectl, pods, containers, or clusters. Triggers include diagnosing CrashLoopBackOff, ImagePullBackOff, OOMKilled, or Pending pods, responding to production incidents, troubleshooting node NotReady or DiskPressure, debugging service connectivity or networking, investigating PVC or storage.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-ahmedasmar-devops-claude-skills-k8s-troubleshooter-skills-skill-md`: Use the immutable source file https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/k8s-troubleshooter/skills/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
