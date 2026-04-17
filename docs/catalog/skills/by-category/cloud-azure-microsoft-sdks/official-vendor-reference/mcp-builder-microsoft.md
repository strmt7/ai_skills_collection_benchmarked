# mcp-builder

Category: Cloud, Azure & Microsoft SDKs

Mirrored skill: `included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/mcp-builder-microsoft`

Agent-ready entrypoint: `included/agent-ready/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/mcp-builder-microsoft/SKILL.md`

Source: [microsoft/skills `.github/skills/mcp-builder/SKILL.md`](https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/skills/mcp-builder/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a2c05249c4a2`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP), Node/TypeScript (MCP SDK), or C#/.NET (Microsoft MCP SDK).

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-microsoft-skills-github-skills-mcp-builder-skill-md`: Use the immutable source file https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/skills/mcp-builder/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `cloud-azure-and-microsoft-sdks-kubernetes-examples`: Validate manifests and operational runbooks.
- `cloud-azure-and-microsoft-sdks-opentelemetry-demo`: Debug telemetry across microservices.
- `cloud-azure-and-microsoft-sdks-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
