# stop-slop

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/reddit-verified-writing-skill/hardikpandya-stop-slop`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/reddit-verified-writing-skill/hardikpandya-stop-slop/SKILL.md`

Source: [hardikpandya/stop-slop `SKILL.md`](https://github.com/hardikpandya/stop-slop/blob/8da1f030185bdfe8471220585162991eaeb970e9/SKILL.md)

Selected ref: `default-branch HEAD`; commit `8da1f030185b`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Remove AI writing patterns from prose. Use when drafting, editing, or reviewing text to eliminate predictable AI tells.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-hardikpandya-stop-slop-skill-md`: Use the immutable source file https://github.com/hardikpandya/stop-slop/blob/8da1f030185bdfe8471220585162991eaeb970e9/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
