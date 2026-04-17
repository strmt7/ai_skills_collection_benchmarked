# youtube-batch-transcript-extractor-api-skill

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-batch-transcript-extractor-api-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/browser-automation-reference/browser-act-skills-youtube-batch-transcript-extractor-api-skill/SKILL.md`

Source: [browser-act/skills `youtube-batch-transcript-extractor-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-batch-transcript-extractor-api-skill/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: This skill helps users automatically extract YouTube video transcripts and metadata in batch via the BrowserAct API. The Agent should proactively apply this skill when users express needs like batch extract full transcripts from YouTube videos for specific keywords, scrape YouTube subtitles for a list of videos, get batch video metadata and likes counts for analysis, automate YouTube search and subtitle extraction,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-youtube-batch-transcript-extractor-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/youtube-batch-transcript-extractor-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
