# sarif-parsing

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-sarif-parsing`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-sarif-parsing/SKILL.md`

Source: [trailofbits/skills `plugins/static-analysis/skills/sarif-parsing/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/sarif-parsing/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Parses and processes SARIF files from static analysis tools like CodeQL, Semgrep, or other scanners. Triggers on "parse sarif", "read scan results", "aggregate findings", "deduplicate alerts", or "process sarif output". Handles filtering, deduplication, format conversion, and CI/CD integration of SARIF data. Does NOT run scans — use the Semgrep or CodeQL skills for that.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-static-analysis-skills-sarif-parsing-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/sarif-parsing/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
