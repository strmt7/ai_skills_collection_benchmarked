# dmux-workflows

Category: Agent infrastructure & skill creation

Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-dmux-workflows`

Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-dmux-workflows/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/dmux-workflows/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/dmux-workflows/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Single-session workflow coordination using dmux (tmux pane manager for AI agents). Patterns for single-session workflow coordination across Claude Code, Codex, OpenCode, and other harnesses. Use when running one AI session or coordinating single-session development workflows.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-dmux-workflows-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/dmux-workflows/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
