# dependency-update-bot

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/reddit-verified-gtm-registry/dependency-update-bot`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/reddit-verified-gtm-registry/dependency-update-bot/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/dependency-update-bot/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/dependency-update-bot/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Scans your project for outdated npm, pip, Cargo, Go, or Ruby packages. Runs a CVE security audit. Fetches changelogs, summarizes breaking changes with Gemini, and opens one PR per risk group (patch, minor, major). Includes Diagnosis Mode for install conflicts. Use when asked to update dependencies, check for outdated packages, open dependency PRs, scan for package updates, audit for CVEs, or flag breaking changes.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-dependency-update-bot-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/dependency-update-bot/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
