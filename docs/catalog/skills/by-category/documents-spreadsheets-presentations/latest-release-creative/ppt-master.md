# ppt-master

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/SKILL.md`

Source: [hugohe3/ppt-master `skills/ppt-master/SKILL.md`](https://github.com/hugohe3/ppt-master/blob/19297c51cce3361d55137f527c010a8886f88bda/skills/ppt-master/SKILL.md)

Selected ref: `v2.3.0`; commit `19297c51cce3`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI-driven multi-format SVG content generation system. Converts source documents (PDF/DOCX/URL/Markdown) into high-quality SVG pages and exports to PPTX through multi-role collaboration. Use when user asks to "create PPT", "make presentation", "生成PPT", "做PPT", "制作演示文稿", or mentions "ppt-master".

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-hugohe3-ppt-master-skills-ppt-master-skill-md`: Use the immutable source file https://github.com/hugohe3/ppt-master/blob/19297c51cce3361d55137f527c010a8886f88bda/skills/ppt-master/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
