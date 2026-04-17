# ai-video-editing

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/creative-reference/raven7979-ai-video-editing-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/creative-reference/raven7979-ai-video-editing-skill/SKILL.md`

Source: [Raven7979/ai-video-editing-skill `SKILL.md`](https://github.com/Raven7979/ai-video-editing-skill/blob/9bf0a9c3396c181dca45ee969de72bfa57602d4c/SKILL.md)

Selected ref: `default-branch HEAD`; commit `9bf0a9c3396c`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: 用于 AI 口播初剪、自动剪辑、去气口、去重复、视频转字幕、按口播稿对稿。支持语义级重复判断、剪后重新转字幕并与口播稿复核，还会标出大段 NG / 试讲 / 临场发挥候选段供用户确认。支持中文和英文，默认按电脑语言自动切换，也可手动指定。中文触发词包括 AI剪辑、自动剪辑、初剪、口播初剪、去气口、视频转字幕、对稿；英文触发词包括 AI video editing、auto edit this video、video edit、rough cut、trim pauses、remove repeated takes。开始前先确认用户是否提供口播稿，以及剪辑强度选 一般 或 多点。

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-raven7979-ai-video-editing-skill-skill-md`: Use the immutable source file https://github.com/Raven7979/ai-video-editing-skill/blob/9bf0a9c3396c181dca45ee969de72bfa57602d4c/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
