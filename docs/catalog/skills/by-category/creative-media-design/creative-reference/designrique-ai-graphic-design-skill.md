# ai-graphic-design

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/designrique-ai-graphic-design-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/designrique-ai-graphic-design-skill/SKILL.md`

Source: [designrique/ai-graphic-design-skill `SKILL.md`](https://github.com/designrique/ai-graphic-design-skill/blob/7d9d03b290f076e51d0b574659cda2ca9347651e/SKILL.md)

Selected ref: `default-branch HEAD`; commit `7d9d03b290f0`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Guide for creating logos, brand identities, and visual assets using AI tools — covers tool selection, prompt engineering, vectorization pipelines, mockups, automation, and IP safety.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-designrique-ai-graphic-design-skill-skill-md`: Use the immutable source file https://github.com/designrique/ai-graphic-design-skill/blob/7d9d03b290f076e51d0b574659cda2ca9347651e/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
