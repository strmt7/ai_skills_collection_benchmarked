# meeting-brief-generator

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-meeting-brief-generator`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-meeting-brief-generator/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/meeting-brief-generator/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/meeting-brief-generator/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Takes a company name and optional contact, runs targeted research via Tavily, synthesizes a 1-page pre-call brief with Gemini, and optionally saves it to Notion. Use when asked to prepare for a meeting, research a prospect before a call, generate a company brief, create a pre-call summary, or write a meeting prep doc. Trigger when a user says "prepare me for a meeting with", "research this company before my call",.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-meeting-brief-generator-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/meeting-brief-generator/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
