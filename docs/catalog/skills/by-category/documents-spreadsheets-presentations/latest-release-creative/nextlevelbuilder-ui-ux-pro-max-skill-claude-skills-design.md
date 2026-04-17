# ckm:design

Category: Documents, spreadsheets & presentations

Mirrored skill: `included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design`

Agent-ready entrypoint: `included/agent-ready/by-category/documents-spreadsheets-presentations/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design/SKILL.md`

Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design/SKILL.md)

Selected ref: `v2.5.0`; commit `07f4ef3ac256`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini AI), corporate identity program (50 deliverables, CIP mockups), HTML presentations (Chart.js), banner design (22 styles, social/ads/web/print), icon design (15 styles, SVG, Gemini 3.1 Pro), social photos (HTML→screenshot, multi-platform). Actions: design logo, create CIP, generate mockups, build slides, design.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `documents-spreadsheets-and-presentations-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `documents-spreadsheets-and-presentations-enron-email`: Classify, summarize, and route real email threads.
- `documents-spreadsheets-and-presentations-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
