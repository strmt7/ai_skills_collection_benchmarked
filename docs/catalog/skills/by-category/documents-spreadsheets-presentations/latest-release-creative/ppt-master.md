# ppt-master

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master/SKILL.md`

Source: [hugohe3/ppt-master `skills/ppt-master/SKILL.md`](https://github.com/hugohe3/ppt-master/blob/a50758ac29ec027e85966db33e2ae80031446756/skills/ppt-master/SKILL.md)

Selected ref: `v6.6.0`; commit `a50758ac29ec`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI-driven presentation workflow for generating editable PPTX decks and slides, reconstructing page visuals, creating reusable Brand/Style/Layout/Deck workspaces, filling native PPTX templates, and enhancing finished PPTX files. Use when the user asks to create, generate, reconstruct, regenerate, beautify, redesign, template, fill, or enhance a presentation, PPT, PPTX, slide deck, or courseware — including adding.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-hugohe3-ppt-master-skills-ppt-master-skill-md`: Use the immutable source file https://github.com/hugohe3/ppt-master/blob/a50758ac29ec027e85966db33e2ae80031446756/skills/ppt-master/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
