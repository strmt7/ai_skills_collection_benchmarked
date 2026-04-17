# create-infographics

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/creative-reference/aizzaku-create-infographics`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/creative-reference/aizzaku-create-infographics/SKILL.md`

Source: [aizzaku/create-infographics `SKILL.md`](https://github.com/aizzaku/create-infographics/blob/5c8c8821026e7ee5998c886780237e64193e54c3/SKILL.md)

Selected ref: `default-branch HEAD`; commit `5c8c8821026e`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Creates production-grade infographics as HTML, PNG, and PDF from any data or brief. Use when asked for an infographic, visual summary, one-pager, data visualization, or to convert tables, stats, timelines, or comparisons into a visual format. Also triggers on: "shareable graphic", "visual report", "poster" + data content, "one-pager", or any request where information should be presented as a designed image. Crypto.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-aizzaku-create-infographics-skill-md`: Use the immutable source file https://github.com/aizzaku/create-infographics/blob/5c8c8821026e7ee5998c886780237e64193e54c3/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Move long background material into references/ to keep SKILL.md concise.
