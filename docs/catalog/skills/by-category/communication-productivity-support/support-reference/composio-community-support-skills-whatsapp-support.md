# whatsapp-support

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/support-reference/composio-community-support-skills-whatsapp-support`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/support-reference/composio-community-support-skills-whatsapp-support/SKILL.md`

Source: [composio-community/support-skills `whatsapp-support/SKILL.md`](https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/whatsapp-support/SKILL.md)

Selected ref: `default-branch HEAD`; commit `b4f842c3cbdc`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Handle WhatsApp customer support conversations via [Wati](https://composio.dev/toolkits/wati) or [Whautomate](https://composio.dev/toolkits/whautomate)

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-composio-community-support-skills-whatsapp-support-skill-md`: Use the immutable source file https://github.com/composio-community/support-skills/blob/b4f842c3cbdcae0c45771fd996c396aee80dde2e/whatsapp-support/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
