# svg-animations

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/reddit-verified-creative-skill/svg-animations`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/reddit-verified-creative-skill/svg-animations/SKILL.md`

Source: [supermemoryai/skills `svg-animations/SKILL.md`](https://github.com/supermemoryai/skills/blob/10d5e16780b446c5ce58968bcde528766699cdf2/svg-animations/SKILL.md)

Selected ref: `default-branch HEAD`; commit `10d5e16780b4`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Create beautiful, performant SVG animations and illustrations. Use this skill when the user asks to create SVG graphics, icons, illustrations, animated logos, path animations, morphing shapes, loading spinners, or any animated SVG content. Covers SMIL animations, CSS-driven SVG animation, path drawing effects, shape morphing, motion paths, gradients, masks, and filters.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-supermemoryai-skills-svg-animations-skill-md`: Use the immutable source file https://github.com/supermemoryai/skills/blob/10d5e16780b446c5ce58968bcde528766699cdf2/svg-animations/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
