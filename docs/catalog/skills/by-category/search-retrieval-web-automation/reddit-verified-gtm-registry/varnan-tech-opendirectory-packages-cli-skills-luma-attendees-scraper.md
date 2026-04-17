# luma-attendees-scraper

Category: Search, retrieval & web automation

Mirrored skill: `included/skills/by-category/search-retrieval-web-automation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-luma-attendees-scraper`

Agent-ready entrypoint: `included/agent-ready/by-category/search-retrieval-web-automation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-luma-attendees-scraper/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/luma-attendees-scraper/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/luma-attendees-scraper/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Browser-console script to export attendee data from a Luma event into a CSV. Use when users ask to scrape or export attendees from a Luma event.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-luma-attendees-scraper-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/luma-attendees-scraper/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `search-retrieval-and-web-automation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.
- `search-retrieval-and-web-automation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `search-retrieval-and-web-automation-ms-marco`: Rank passages and support answer extraction.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
