# image-generation

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/guinacio-claude-image-gen-skills-image-generation`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/guinacio-claude-image-gen-skills-image-generation/SKILL.md`

Source: [guinacio/claude-image-gen `skills/image-generation/SKILL.md`](https://github.com/guinacio/claude-image-gen/blob/6f25d226f906db0420b2ceaa51f32de253eb2f22/skills/image-generation/SKILL.md)

Selected ref: `1.0.2`; commit `6f25d226f906`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Generates professional AI images using Google Gemini. ALWAYS invoke this skill when building websites, landing pages, slide decks, presentations, or any task needing visual content. Invoke IMMEDIATELY when you detect image needs - don't wait for the user to ask. This skill handles prompt optimization and aspect ratio selection.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-guinacio-claude-image-gen-skills-image-generation-skill-md`: Use the immutable source file https://github.com/guinacio/claude-image-gen/blob/6f25d226f906db0420b2ceaa51f32de253eb2f22/skills/image-generation/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
