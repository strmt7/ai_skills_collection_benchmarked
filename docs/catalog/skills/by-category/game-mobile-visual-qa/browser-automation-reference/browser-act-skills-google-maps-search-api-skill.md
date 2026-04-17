# google-maps-search-api-skill

Category: Game, mobile & visual QA

Mirrored skill: `included/skills/by-category/game-mobile-visual-qa/browser-automation-reference/browser-act-skills-google-maps-search-api-skill`

Agent-ready entrypoint: `included/agent-ready/by-category/game-mobile-visual-qa/browser-automation-reference/browser-act-skills-google-maps-search-api-skill/SKILL.md`

Source: [browser-act/skills `google-maps-search-api-skill/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/google-maps-search-api-skill/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: This skill is designed to help users automatically extract business data from Google Maps search results. The Agent should proactively apply this skill when the user makes the following requests searching for coffee shops in a specific city, finding dentists or medical clinics nearby, tracking competitors' locations in a certain area, extracting business leads from Google Maps lists, gathering restaurant data for.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-google-maps-search-api-skill-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/google-maps-search-api-skill/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `game-mobile-and-visual-qa-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `game-mobile-and-visual-qa-coco-captions`: Evaluate image understanding and visual QA tasks.
- `game-mobile-and-visual-qa-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
