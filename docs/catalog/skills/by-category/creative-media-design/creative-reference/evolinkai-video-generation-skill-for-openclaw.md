# evolink-video

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/evolinkai-video-generation-skill-for-openclaw`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/evolinkai-video-generation-skill-for-openclaw/SKILL.md`

Source: [EvoLinkAI/video-generation-skill-for-openclaw `SKILL.md`](https://github.com/EvoLinkAI/video-generation-skill-for-openclaw/blob/83723cdfa9d43eb8dd79287651f0e3e291802e90/SKILL.md)

Selected ref: `default-branch HEAD`; commit `83723cdfa9d4`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: AI video generation — Sora, Kling, Veo 3, Seedance, Hailuo, WAN, Grok. Text-to-video, image-to-video, video editing. 37 models, one API key.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-evolinkai-video-generation-skill-for-openclaw-skill-md`: Use the immutable source file https://github.com/EvoLinkAI/video-generation-skill-for-openclaw/blob/83723cdfa9d43eb8dd79287651f0e3e291802e90/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
