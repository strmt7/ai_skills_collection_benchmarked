# agent-media

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/agent-media`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/agent-media/SKILL.md`

Source: [yuvalsuede/agent-media-skill `SKILL.md`](https://github.com/yuvalsuede/agent-media-skill/blob/c37c209942bad44588f4d93b744473d733f95e6d/SKILL.md)

Selected ref: `default-branch HEAD`; commit `c37c209942ba`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI UGC video production from the terminal using the `agent-media` CLI.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-yuvalsuede-agent-media-skill-skill-md`: Use the immutable source file https://github.com/yuvalsuede/agent-media-skill/blob/c37c209942bad44588f4d93b744473d733f95e6d/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
