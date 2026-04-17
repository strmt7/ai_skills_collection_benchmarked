# pathml

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-pathml`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-pathml/SKILL.md`

Source: [K-Dense-AI/scientific-agent-skills `scientific-skills/pathml/SKILL.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/pathml/SKILL.md)

Selected ref: `v2.37.1`; commit `eb20fb0dcb0b`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Full-featured computational pathology toolkit. Use for advanced WSI analysis including multiplexed immunofluorescence (CODEX, Vectra), nucleus segmentation, tissue graph construction, and ML model training on pathology data. Supports 160+ slide formats. For simple tile extraction from H&E slides, histolab may be simpler.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-k-dense-ai-scientific-agent-skills-scientific-skills-pathml-skill-md`: Use the immutable source file https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/pathml/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
