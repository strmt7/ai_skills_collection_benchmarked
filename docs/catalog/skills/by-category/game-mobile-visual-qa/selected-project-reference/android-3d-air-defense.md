# android-3d-air-defense

Category: Game, mobile & visual QA

Mirrored skill: `included/skills/by-category/game-mobile-visual-qa/selected-project-reference/android-3d-air-defense`

Agent-ready entrypoint: `included/agent-ready/by-category/game-mobile-visual-qa/selected-project-reference/android-3d-air-defense/SKILL.md`

Source: [strmt7/project_air_defense `skills/android-3d-air-defense/SKILL.md`](https://github.com/strmt7/project_air_defense/blob/77f082fe23a86ded15e696a22955b2a890da2fce/skills/android-3d-air-defense/SKILL.md)

Selected ref: `default-branch HEAD`; commit `77f082fe23a8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Use this skill when building, debugging, balancing, profiling, or visually upgrading the Project Air Defense Android 3D missile-defense prototype, especially for libGDX battle flow, mobile rendering quality, interception logic, HUD ergonomics, and emulator-verified Android fixes.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-project-air-defense-skills-android-3d-air-defense-skill-md`: Use the immutable source file https://github.com/strmt7/project_air_defense/blob/77f082fe23a86ded15e696a22955b2a890da2fce/skills/android-3d-air-defense/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `game-mobile-and-visual-qa-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `game-mobile-and-visual-qa-coco-captions`: Evaluate image understanding and visual QA tasks.
- `game-mobile-and-visual-qa-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
