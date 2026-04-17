# internal-comms

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/official-reference/anthropics-skills-skills-internal-comms`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/official-reference/anthropics-skills-skills-internal-comms/SKILL.md`

Source: [anthropics/skills `skills/internal-comms/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/internal-comms/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: A set of resources to help me write all kinds of internal communications, using the formats that my company likes to use. Claude should use this skill whenever asked to write some sort of internal communications (status reports, leadership updates, 3P updates, company newsletters, FAQs, incident reports, project updates, etc.).

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-internal-comms-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/internal-comms/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
