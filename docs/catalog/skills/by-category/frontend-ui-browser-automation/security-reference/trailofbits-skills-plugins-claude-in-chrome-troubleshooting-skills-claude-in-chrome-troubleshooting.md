# claude-in-chrome-troubleshooting

Category: Frontend, UI & browser automation

Mirrored skill: `included/skills/by-category/frontend-ui-browser-automation/security-reference/trailofbits-skills-plugins-claude-in-chrome-troubleshooting-skills-claude-in-chrome-troubleshooting`

Agent-ready entrypoint: `included/agent-ready/by-category/frontend-ui-browser-automation/security-reference/trailofbits-skills-plugins-claude-in-chrome-troubleshooting-skills-claude-in-chrome-troubleshooting/SKILL.md`

Source: [trailofbits/skills `plugins/claude-in-chrome-troubleshooting/skills/claude-in-chrome-troubleshooting/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/claude-in-chrome-troubleshooting/skills/claude-in-chrome-troubleshooting/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Diagnose and fix Claude in Chrome MCP extension connectivity issues. Use when mcp__claude-in-chrome__* tools fail, return "Browser extension is not connected", or behave erratically.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-claude-in-chrome-troubleshooting-skills-claude-in-chrome-troubleshooting-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/claude-in-chrome-troubleshooting/skills/claude-in-chrome-troubleshooting/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `frontend-ui-and-browser-automation-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.
- `frontend-ui-and-browser-automation-coco-captions`: Evaluate image understanding and visual QA tasks.
- `frontend-ui-and-browser-automation-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
