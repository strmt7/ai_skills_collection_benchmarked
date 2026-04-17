---
name: "audit-augmentation"
description: "Augments Trailmark code graphs with external audit findings from SARIF static analysis results and weAudit annotation files. Maps findings to graph nodes by file and line overlap, creates severity-based subgraphs, and enables cross-referencing findings with pre-analysis data (blast radius, taint, etc.). Use when projecting SARIF results onto a code graph, overlaying weAudit annotations, cross-referencing Semgrep or."
source_skill_id: "trailofbits-skills-plugins-trailmark-skills-audit-augmentation-skill-md"
category: "Security, compliance & risk"
source_mirror: "../../../../../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation/SKILL.md"
benchmark_status: "artifact_gated"
---

# audit-augmentation

Use this skill when the task matches the description above or the source path clearly applies. Start with this concise entrypoint; open `../../../../../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation/SKILL.md` only when implementation details, commands, assets, or references are needed.

## Workflow

1. Confirm the task matches this skill's scope.
2. Read the local source mirror if more detail is required.
3. Follow repository-level `AGENTS.md`; use one AI session only.
4. Keep claims tied to files, commands, citations, or benchmark artifacts.

## Verification

- Source mirror: `../../../../../skills/by-category/security-compliance-risk/security-reference/trailofbits-skills-plugins-trailmark-skills-audit-augmentation/SKILL.md`
- Source commit: `e8cc5baf9329ccb491bfa200e82eacbac83b1ead`
- Static benchmark results: see `docs/benchmark-results.md`
- Runtime artifacts recorded by this entrypoint: `0`
- Assigned scenarios: `skill-proof-trailofbits-skills-plugins-trailmark-skills-audit-augmentation-skill-md`, `security-compliance-and-risk-owasp-benchmark`, `security-compliance-and-risk-owasp-juice-shop`, `security-compliance-and-risk-kubernetes-examples`

Do not claim this skill passed a runtime benchmark until a validated artifact exists.
