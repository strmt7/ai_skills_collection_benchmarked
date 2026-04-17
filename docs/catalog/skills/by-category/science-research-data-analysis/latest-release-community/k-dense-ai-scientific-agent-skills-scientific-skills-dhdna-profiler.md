# dhdna-profiler

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-dhdna-profiler`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-dhdna-profiler/SKILL.md`

Source: [K-Dense-AI/scientific-agent-skills `scientific-skills/dhdna-profiler/SKILL.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/dhdna-profiler/SKILL.md)

Selected ref: `v2.37.1`; commit `eb20fb0dcb0b`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Extract cognitive patterns and thinking fingerprints from any text. Use this skill when the user wants to analyze how someone thinks, understand cognitive style, profile writing or speech patterns, compare thinking styles between people, asks "what's my thinking style", "analyze how this person reasons", "cognitive profile", "thinking pattern", "DHDNA", "digital DNA", or wants to understand the mind behind any.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-k-dense-ai-scientific-agent-skills-scientific-skills-dhdna-profiler-skill-md`: Use the immutable source file https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/dhdna-profiler/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
