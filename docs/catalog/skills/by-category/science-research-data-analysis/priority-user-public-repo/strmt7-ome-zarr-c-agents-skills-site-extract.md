# site-extract

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-site-extract`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/priority-user-public-repo/strmt7-ome-zarr-c-agents-skills-site-extract/SKILL.md`

Source: [strmt7/ome-zarr-C `.agents/skills/site-extract/SKILL.md`](https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/site-extract/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a9238a81742f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Extract the smallest useful amount of text or structured data from a known public page before falling back to full browser automation.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-ome-zarr-c-agents-skills-site-extract-skill-md`: Use the immutable source file https://github.com/strmt7/ome-zarr-C/blob/a9238a81742f96c89acf6d83fce6d6b882ac4d1c/.agents/skills/site-extract/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add an executable validator or helper script so the workflow has objective checks.
