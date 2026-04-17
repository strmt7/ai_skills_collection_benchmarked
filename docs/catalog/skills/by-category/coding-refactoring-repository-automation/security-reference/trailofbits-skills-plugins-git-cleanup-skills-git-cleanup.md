# git-cleanup

Category: Coding, refactoring & repository automation

Mirrored skill: `included/skills/by-category/coding-refactoring-repository-automation/security-reference/trailofbits-skills-plugins-git-cleanup-skills-git-cleanup`

Agent-ready entrypoint: `included/agent-ready/by-category/coding-refactoring-repository-automation/security-reference/trailofbits-skills-plugins-git-cleanup-skills-git-cleanup/SKILL.md`

Source: [trailofbits/skills `plugins/git-cleanup/skills/git-cleanup/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/git-cleanup/skills/git-cleanup/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Safely analyzes and cleans up local git branches and worktrees by categorizing them as merged, squash-merged, superseded, or active work.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-git-cleanup-skills-git-cleanup-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/git-cleanup/skills/git-cleanup/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `coding-refactoring-and-repository-automation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `coding-refactoring-and-repository-automation-kubernetes-examples`: Validate manifests and operational runbooks.
- `coding-refactoring-and-repository-automation-opentelemetry-demo`: Debug telemetry across microservices.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
