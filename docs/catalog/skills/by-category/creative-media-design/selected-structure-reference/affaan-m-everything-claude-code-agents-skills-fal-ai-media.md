# fal-ai-media

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-fal-ai-media`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-fal-ai-media/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/fal-ai-media/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/fal-ai-media/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Unified media generation via fal.ai MCP — image, video, and audio. Covers text-to-image (Nano Banana), text/image-to-video (Seedance, Kling, Veo 3), text-to-speech (CSM-1B), and video-to-audio (ThinkSound). Use when the user wants to generate images, videos, or audio with AI.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-fal-ai-media-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/fal-ai-media/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
