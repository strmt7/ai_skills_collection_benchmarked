# workflow-supply-chain-maintenance

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-workflow-supply-chain-maintenance`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-workflow-supply-chain-maintenance/SKILL.md`

Source: [strmt7/ome-zarr-C `.agents/skills/workflow-supply-chain-maintenance/SKILL.md`](https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/workflow-supply-chain-maintenance/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a9238a81742f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Use when editing GitHub Actions, CodeQL, Dependabot, or workflow-installed tool pins and the repo needs verified current versions and scanner scope discipline.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-ome-zarr-c-agents-skills-workflow-supply-chain-maintenance-skill-md`: Use the immutable source file https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/workflow-supply-chain-maintenance/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
