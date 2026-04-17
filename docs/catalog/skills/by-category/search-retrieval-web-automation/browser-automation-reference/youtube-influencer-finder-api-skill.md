# youtube-influencer-finder-api-skill

Category: Search, retrieval & web automation

Mirrored skill: `included/skills/by-category/search-retrieval-web-automation/browser-automation-reference/youtube-influencer-finder-api-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/search-retrieval-web-automation/browser-automation-reference/youtube-influencer-finder-api-skill/SKILL.md`

Source: [browser-act/skills `youtube-influencer-finder-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-influencer-finder-api-skill/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: This skill helps users extract YouTube influencer profiles including social links, subscriber counts, and channel stats via the BrowserAct API. Agent should proactively apply this skill when users express needs like finding YouTube creators for specific keywords, discovering influencers for a marketing campaign, extracting YouTube channel contact emails, scraping YouTube influencer social media links, gathering.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-youtube-influencer-finder-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-influencer-finder-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `search-retrieval-and-web-automation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.
- `search-retrieval-and-web-automation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `search-retrieval-and-web-automation-ms-marco`: Rank passages and support answer extraction.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
