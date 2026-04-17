# web-artifacts-builder

Category: Search, retrieval & web automation

Mirrored skill: `included/skills/by-category/search-retrieval-web-automation/official-reference/anthropics-skills-skills-web-artifacts-builder`

Agent-ready entrypoint: `included/agent-ready/by-category/search-retrieval-web-automation/official-reference/anthropics-skills-skills-web-artifacts-builder/SKILL.md`

Source: [anthropics/skills `skills/web-artifacts-builder/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/web-artifacts-builder/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using modern frontend web technologies (React, Tailwind CSS, shadcn/ui). Use for complex artifacts requiring state management, routing, or shadcn/ui components - not for simple single-file HTML/JSX artifacts.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-web-artifacts-builder-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/web-artifacts-builder/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `search-retrieval-and-web-automation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.
- `search-retrieval-and-web-automation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `search-retrieval-and-web-automation-ms-marco`: Rank passages and support answer extraction.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
