# browser-fallback

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-browser-fallback`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-browser-fallback/SKILL.md`

Source: [strmt7/ome-zarr-C `.agents/skills/browser-fallback/SKILL.md`](https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/browser-fallback/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a9238a81742f`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Use a deterministic browser workflow only when direct fetch or extraction is insufficient for a public-web task.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-ome-zarr-c-agents-skills-browser-fallback-skill-md`: Use the immutable source file https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/browser-fallback/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add an executable validator or helper script so the workflow has objective checks.
