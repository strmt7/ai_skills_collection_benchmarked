# pufferlib

Category: Game, mobile & visual QA

Mirrored skill: `included/skills/by-category/game-mobile-visual-qa/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-pufferlib`

Agent-ready entrypoint: `included/agent-ready/by-category/game-mobile-visual-qa/latest-release-community/k-dense-ai-scientific-agent-skills-scientific-skills-pufferlib/SKILL.md`

Source: [K-Dense-AI/scientific-agent-skills `scientific-skills/pufferlib/SKILL.md`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/pufferlib/SKILL.md)

Selected ref: `v2.37.1`; commit `eb20fb0dcb0b`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: High-performance reinforcement learning framework optimized for speed and scale. Use when you need fast parallel training, vectorized environments, single-session systems, or integration with game environments (Atari, Procgen, NetHack). Achieves 2-10x speedups over standard implementations. For quick prototyping or standard algorithm implementations with extensive documentation, use stable-baselines3 instead.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-k-dense-ai-scientific-agent-skills-scientific-skills-pufferlib-skill-md`: Use the immutable source file https://github.com/K-Dense-AI/scientific-agent-skills/blob/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/scientific-skills/pufferlib/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `game-mobile-and-visual-qa-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `game-mobile-and-visual-qa-coco-captions`: Evaluate image understanding and visual QA tasks.
- `game-mobile-and-visual-qa-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
