# ue5-commonui-menu-systems

Category: Game, mobile & visual QA

Mirrored skill: `included/skills/by-category/game-mobile-visual-qa/priority-user-public-repo/strmt7-project-air-defense-agents-skills-ue5-commonui-menu-systems`

Agent-ready entrypoint: `included/agent-ready/by-category/game-mobile-visual-qa/priority-user-public-repo/strmt7-project-air-defense-agents-skills-ue5-commonui-menu-systems/SKILL.md`

Source: [strmt7/project_air_defense `.agents/skills/ue5-commonui-menu-systems/SKILL.md`](https://github.com/strmt7/project_air_defense/blob/77f082fe23a86ded15e696a22955b2a890da2fce/.agents/skills/ue5-commonui-menu-systems/SKILL.md)

Selected ref: `default-branch HEAD`; commit `77f082fe23a8`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Use when changing a major UE5 front-end menu, options flow, modal stack, routed input surface, or layered smartphone-first menu architecture. Applies to CommonUI adoption decisions, activatable-widget stacks, menu settings flows, and player-facing mobile front-end structure.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-project-air-defense-agents-skills-ue5-commonui-menu-systems-skill-md`: Use the immutable source file https://github.com/strmt7/project_air_defense/blob/77f082fe23a86ded15e696a22955b2a890da2fce/.agents/skills/ue5-commonui-menu-systems/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `game-mobile-and-visual-qa-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `game-mobile-and-visual-qa-coco-captions`: Evaluate image understanding and visual QA tasks.
- `game-mobile-and-visual-qa-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
