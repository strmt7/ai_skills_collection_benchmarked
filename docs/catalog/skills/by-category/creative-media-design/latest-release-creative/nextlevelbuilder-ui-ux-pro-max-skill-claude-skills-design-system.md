# ckm:design-system

Category: Creative, media & design

Mirrored skill: `included/skills/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system`

Agent-ready entrypoint: `included/agent-ready/by-category/creative-media-design/latest-release-creative/nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system/SKILL.md`

Source: [nextlevelbuilder/ui-ux-pro-max-skill `.claude/skills/design-system/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design-system/SKILL.md)

Selected ref: `v2.5.0`; commit `07f4ef3ac256`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacing/typography scales, component specs, strategic slide creation. Use for design tokens, systematic design, brand-compliant presentations.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-nextlevelbuilder-ui-ux-pro-max-skill-claude-skills-design-system-skill-md`: Use the immutable source file https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4/.claude/skills/design-system/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `creative-media-and-design-coco-captions`: Evaluate image understanding and visual QA tasks.
- `creative-media-and-design-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `creative-media-and-design-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
