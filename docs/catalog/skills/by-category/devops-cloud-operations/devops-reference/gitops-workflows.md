# gitops-workflows

Category: DevOps, cloud & operations

Mirrored skill: `included/skills/by-category/devops-cloud-operations/devops-reference/gitops-workflows`

Agent-ready entrypoint: `included/agent-ready/by-category/devops-cloud-operations/devops-reference/gitops-workflows/SKILL.md`

Source: [ahmedasmar/devops-claude-skills `gitops-workflows/skills/SKILL.md`](https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/gitops-workflows/skills/SKILL.md)

Selected ref: `default-branch HEAD`; commit `1489c33ad882`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: GitOps deployment workflows with ArgoCD and Flux. Use this skill whenever the user mentions GitOps, ArgoCD, Flux, Flagger, Argo Rollouts, or continuous deployment to Kubernetes. Triggers include setting up ArgoCD or Flux from scratch, designing Git repository structures (monorepo vs polyrepo, app-of-apps), deploying to multiple clusters with ApplicationSets, managing secrets in Git (SOPS, Sealed Secrets, External.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-ahmedasmar-devops-claude-skills-gitops-workflows-skills-skill-md`: Use the immutable source file https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/gitops-workflows/skills/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `devops-cloud-and-operations-kubernetes-examples`: Validate manifests and operational runbooks.
- `devops-cloud-and-operations-opentelemetry-demo`: Debug telemetry across microservices.
- `devops-cloud-and-operations-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
