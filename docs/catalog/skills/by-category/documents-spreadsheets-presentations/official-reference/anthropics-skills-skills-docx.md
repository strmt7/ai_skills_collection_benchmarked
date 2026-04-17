# docx

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/anthropics-skills-skills-docx`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/anthropics-skills-skills-docx/SKILL.md`

Source: [anthropics/skills `skills/docx/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/docx/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx files). Triggers include: any mention of 'Word doc', 'word document', '.docx', or requests to produce professional documents with formatting like tables of contents, headings, page numbers, or letterheads. Also use when extracting or reorganizing content from .docx files, inserting or replacing images in documents,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-docx-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/docx/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Move long background material into references/ to keep SKILL.md concise.
