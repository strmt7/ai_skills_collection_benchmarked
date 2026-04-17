# treatment-plans

Category: Science, research & data analysis

Mirrored skill: `included/skills/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-treatment-plans`

Agent-ready entrypoint: `included/agent-ready/by-category/science-research-data-analysis/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-treatment-plans/SKILL.md`

Source: [K-Dense-AI/scientific-agent-skills `scientific-skills/treatment-plans/SKILL.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/treatment-plans/SKILL.md)

Selected ref: `v2.37.1`; commit `eb20fb0dcb0b`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Generate concise (3-4 page), focused medical treatment plans in LaTeX/PDF format for all clinical specialties. Supports general medical treatment, rehabilitation therapy, mental health care, chronic disease management, perioperative care, and pain management. Includes SMART goal frameworks, evidence-based interventions with minimal text citations, regulatory compliance (HIPAA), and professional formatting..

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-k-dense-ai-scientific-agent-skills-scientific-skills-treatment-plans-skill-md`: Use the immutable source file https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/treatment-plans/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `science-research-and-data-analysis-cellxgene-census`: Query and analyze single-cell expression data.
- `science-research-and-data-analysis-chembl`: Retrieve molecular bioactivity records.
- `science-research-and-data-analysis-ome-ngff-samples`: Read and validate multiscale microscopy data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Move long background material into references/ to keep SKILL.md concise.
