# semgrep

Category: Security, compliance & risk

Mirrored skill: `included/skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-semgrep`

Agent-ready entrypoint: `included/agent-ready/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-static-analysis-skills-semgrep/SKILL.md`

Source: [trailofbits/skills `plugins/static-analysis/skills/semgrep/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/semgrep/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Run Semgrep static analysis scan on a codebase using parallel subagents. Supports two scan modes — "run all" (full ruleset coverage) and "important only" (high-confidence security vulnerabilities). Automatically detects and uses Semgrep Pro for cross-file taint analysis when available. Use when asked to scan code for vulnerabilities, run a security audit with Semgrep, find bugs, or perform static analysis. Spawns.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-static-analysis-skills-semgrep-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/static-analysis/skills/semgrep/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `security-compliance-and-risk-owasp-benchmark`: Find and classify vulnerability test cases.
- `security-compliance-and-risk-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `security-compliance-and-risk-kubernetes-examples`: Validate manifests and operational runbooks.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
