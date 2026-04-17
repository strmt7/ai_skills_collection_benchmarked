# vgl

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-vgl`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-vgl/SKILL.md`

Source: [Bria-AI/bria-skill `skills/vgl/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/vgl/SKILL.md)

Selected ref: `v1.3.1`; commit `b0e107b0f466`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Maximum control over AI image generation — write structured VGL (Visual Generation Language) JSON that explicitly controls every visual attribute. Define exact object placement, lighting direction, camera angle, lens focal length, composition, color scheme, and artistic style as deterministic JSON instead of ambiguous natural language. Use this skill when you need reproducible image generation, precise control over.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-bria-ai-bria-skill-skills-vgl-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/vgl/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
