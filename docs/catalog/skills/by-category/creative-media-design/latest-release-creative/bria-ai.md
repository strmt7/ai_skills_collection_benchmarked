# bria-ai

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai/SKILL.md`

Source: [Bria-AI/bria-skill `skills/bria-ai/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/bria-ai/SKILL.md)

Selected ref: `v1.3.1`; commit `b0e107b0f466`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI image generation, editing, and background removal API via Bria.ai — remove backgrounds to get transparent PNGs and cutouts, generate images from text prompts, and edit photos with natural language instructions. Also create product photography and lifestyle shots, replace or blur backgrounds, upscale resolution, restyle, and batch-generate visual assets. Use this skill whenever the user wants to remove a.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-bria-ai-bria-skill-skills-bria-ai-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/bria-ai/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
