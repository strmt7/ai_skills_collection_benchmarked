# github-project-contributor-finder-api-skill

Category: Search, retrieval & web automation

Mirrored skill: `included/skills/by-category/search-retrieval-web-automation/browser-automation-reference/browser-act-skills-github-project-contributor-finder-api-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/search-retrieval-web-automation/browser-automation-reference/browser-act-skills-github-project-contributor-finder-api-skill/SKILL.md`

Source: [browser-act/skills `github-project-contributor-finder-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/github-project-contributor-finder-api-skill/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: This skill helps users extract GitHub repository project details and contributor contact information using keywords, stars, and update dates. Agent should proactively apply this skill when users express needs like search for GitHub projects by keywords, find top open-source contributors in specific domains, extract developer contacts from GitHub repositories, discover trending repositories with high stars, gather.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-github-project-contributor-finder-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/github-project-contributor-finder-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `search-retrieval-and-web-automation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.
- `search-retrieval-and-web-automation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `search-retrieval-and-web-automation-ms-marco`: Rank passages and support answer extraction.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
