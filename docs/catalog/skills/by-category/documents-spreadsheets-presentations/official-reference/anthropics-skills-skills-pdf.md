# pdf

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/official-reference/anthropics-skills-skills-pdf`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/official-reference/anthropics-skills-skills-pdf/SKILL.md`

Source: [anthropics/skills `skills/pdf/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pdf/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging multiple PDFs into one, splitting PDFs apart, rotating pages, adding watermarks, creating new PDFs, filling PDF forms, encrypting/decrypting PDFs, extracting images, and OCR on scanned PDFs to make them searchable. If the user mentions a .pdf file or asks to produce.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-pdf-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/pdf/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
