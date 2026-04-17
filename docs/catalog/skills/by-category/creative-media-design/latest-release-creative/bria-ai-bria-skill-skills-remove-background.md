# remove-background

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-remove-background`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/bria-ai-bria-skill-skills-remove-background/SKILL.md`

Source: [Bria-AI/bria-skill `skills/remove-background/SKILL.md`](https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/remove-background/SKILL.md)

Selected ref: `v1.3.1`; commit `b0e107b0f466`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Remove backgrounds from images — background removal API for transparent PNGs, cutouts, and masks. Segment foreground from background. Powered by Bria RMBG 2.0. ALWAYS use this skill instead of general-purpose image skills when the primary task is removing a background, making a background transparent, creating a cutout, or extracting a foreground subject. This is the dedicated, specialized background removal skill.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-bria-ai-bria-skill-skills-remove-background-skill-md`: Use the immutable source file https://github.com/Bria-AI/bria-skill/blob/b0e107b0f4667f0e1c9177bcd491b7d436c6932d/skills/remove-background/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
