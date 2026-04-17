# mcp-builder

Category: Agent infrastructure & skill creation

Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/official-reference/mcp-builder-anthropics`

Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/official-reference/mcp-builder-anthropics/SKILL.md`

Source: [anthropics/skills `skills/mcp-builder/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/mcp-builder/SKILL.md)

Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-anthropics-skills-skills-mcp-builder-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/mcp-builder/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
