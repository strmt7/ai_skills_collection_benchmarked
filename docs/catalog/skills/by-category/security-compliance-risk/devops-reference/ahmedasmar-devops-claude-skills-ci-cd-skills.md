# ci-cd

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/devops-reference/ahmedasmar-devops-claude-skills-ci-cd-skills`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/devops-reference/ahmedasmar-devops-claude-skills-ci-cd-skills/SKILL.md`

Source: [ahmedasmar/devops-claude-skills `ci-cd/skills/SKILL.md`](https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/ci-cd/skills/SKILL.md)

Selected ref: `default-branch HEAD`; commit `1489c33ad882`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: CI/CD pipeline design, optimization, DevSecOps security scanning, and troubleshooting. Use this skill whenever the user mentions CI/CD, GitHub Actions, GitLab CI, pipelines, workflows, builds, or DevSecOps. Triggers include creating new CI/CD workflows, debugging pipeline failures or flaky tests, implementing SAST/DAST/SCA security scanning, optimizing slow builds with caching or parallelization, setting up.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-ahmedasmar-devops-claude-skills-ci-cd-skills-skill-md`: Use the immutable source file https://github.com/ahmedasmar/devops-claude-skills/blob/1489c33ad8829a11219e423327d6b59f8339cee4/ci-cd/skills/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
