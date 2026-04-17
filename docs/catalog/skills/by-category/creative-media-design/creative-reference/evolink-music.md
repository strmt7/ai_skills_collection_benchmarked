# evolink-music

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/evolink-music`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/evolink-music/SKILL.md`

Source: [EvoLinkAI/music-generation-skill-for-openclaw `SKILL.md`](https://github.com/EvoLinkAI/music-generation-skill-for-openclaw/blob/a37e5b6ef986c952d0d5ba57ddc6e6f0c3abd858/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a37e5b6ef986`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: AI music generation with Suno v4, v4.5, v5. Text-to-music, custom lyrics, instrumental, vocal control. 5 models, one API key.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-evolinkai-music-generation-skill-for-openclaw-skill-md`: Use the immutable source file https://github.com/EvoLinkAI/music-generation-skill-for-openclaw/blob/a37e5b6ef986c952d0d5ba57ddc6e6f0c3abd858/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
