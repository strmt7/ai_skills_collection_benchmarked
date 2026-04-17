---
name: workflow-supply-chain-maintenance
description: Use when editing GitHub Actions, CodeQL, Dependabot, or workflow-installed tool pins and the repo needs verified current versions and scanner scope discipline.
origin: repo-local, grounded in official GitHub docs and official release sources
---

# Workflow And Supply Chain Maintenance

Use this skill before changing workflow action versions, CodeQL scope,
Dependabot policy, or workflow-installed tool versions.

## Rules

- Verify workflow action versions from the official GitHub release source, not
  from examples copied out of old READMEs.
- Verify Python tool versions from the canonical package index before updating
  pins in workflows or `pyproject.toml`.
- Keep frozen upstream snapshot directories matching `source_code_v*/` excluded
  from security scanning.
- Prefer a dedicated CodeQL config file for scan scope and query policy so the
  workflow stays small and future snapshot updates have one source of truth.
- Keep Dependabot enabled for every workflow/package ecosystem actually in use.

Read `references/official-guidance.md` before changing workflow pins, CodeQL
scope, or Dependabot configuration.
