# torch-geometric

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/latest-release-community/torch-geometric`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/latest-release-community/torch-geometric/SKILL.md`

Source: [K-Dense-AI/scientific-agent-skills `scientific-skills/torch-geometric/SKILL.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/torch-geometric/SKILL.md)

Selected ref: `v2.37.1`; commit `eb20fb0dcb0b`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Guide for building Graph Neural Networks with PyTorch Geometric (PyG). Use this skill whenever the user asks about graph neural networks, GNNs, node classification, link prediction, graph classification, message passing networks, heterogeneous graphs, neighbor sampling, or any task involving torch_geometric / PyG. Also trigger when you see imports from torch_geometric, or the user mentions graph convolutions (GCN,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-k-dense-ai-scientific-agent-skills-scientific-skills-torch-geometric-skill-md`: Use the immutable source file https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/torch-geometric/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
