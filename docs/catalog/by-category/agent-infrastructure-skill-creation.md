# Agent infrastructure & skill creation

## show-hn-writer - Varnan-Tech/opendirectory `packages/cli/skills/show-hn-writer/SKILL.md`

- Skill page: [varnan-tech-opendirectory-packages-cli-skills-show-hn-writer](../skills/by-category/agent-infrastructure-skill-creation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer/SKILL.md`
- Source: [Varnan-Tech/opendirectory `packages/cli/skills/show-hn-writer/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/show-hn-writer/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`
- What it covers: Catalog summary: Use for show-hn-writer workflows. Source sections include Show HN Writer, Step 1: Gather Project Context, Step 2: Read Context Files (if available).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Show HN Writer, Step 1: Gather Project Context, Step 2: Read Context Files (if available), Step 3: Draft the Title, Step 4: Draft the Body. Resources: has_references.
- Notability: Included from Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/show-hn-writer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## claude-api - affaan-m/everything-claude-code `.agents/skills/claude-api/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-claude-api](../skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-claude-api.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-claude-api`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-claude-api/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/claude-api/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/claude-api/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Anthropic Claude API patterns for Python and TypeScript. Covers Messages API, streaming, tool use, vision, extended thinking, batches, prompt caching, and Claude Agent SDK. Use when building applications with the Claude API or Anthropic SDKs.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Claude API, When to Activate, Model Selection, Python SDK, Installation. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-claude-api-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/claude-api/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## dmux-workflows - affaan-m/everything-claude-code `.agents/skills/dmux-workflows/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-dmux-workflows](../skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-dmux-workflows.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-dmux-workflows`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-dmux-workflows/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/dmux-workflows/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/dmux-workflows/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Single-session workflow coordination using dmux (tmux pane manager for AI agents). Patterns for single-session workflow coordination across Claude Code, Codex, OpenCode, and other harnesses. Use when running one AI session or coordinating single-session development workflows.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: dmux Workflows, When to Activate, What is dmux, Quick Start, Start dmux session. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-dmux-workflows-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/dmux-workflows/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## mcp-server-patterns - affaan-m/everything-claude-code `.agents/skills/mcp-server-patterns/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-mcp-server-patterns](../skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-mcp-server-patterns.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-mcp-server-patterns`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-mcp-server-patterns/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/mcp-server-patterns/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/mcp-server-patterns/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Build MCP servers with Node/TypeScript SDK — tools, resources, prompts, Zod validation, stdio vs Streamable HTTP. Use Context7 or official MCP docs for latest API.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: MCP Server Patterns, When to Use, How It Works, Core concepts, Connecting with stdio. Resources: none observed.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-mcp-server-patterns-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/mcp-server-patterns/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## strategic-compact - affaan-m/everything-claude-code `.agents/skills/strategic-compact/SKILL.md`

- Skill page: [affaan-m-everything-claude-code-agents-skills-strategic-compact](../skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-strategic-compact.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-strategic-compact`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-strategic-compact/SKILL.md`
- Source: [affaan-m/everything-claude-code `.agents/skills/strategic-compact/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/strategic-compact/SKILL.md)
- Selected ref: `v1.10.0`; commit `846ffb75da9a`
- What it covers: Catalog summary: Suggests manual context compaction at logical intervals to preserve context through task phases rather than arbitrary auto-compaction.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Strategic Compact Skill, When to Activate, Why Strategic Compaction?, How It Works, Hook Setup. Resources: has_agents_metadata.
- Notability: Included from selected repository structure reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Assigned benchmark scenarios:
  - `skill-proof-affaan-m-everything-claude-code-agents-skills-strategic-compact-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/strategic-compact/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## mcp-builder - anthropics/skills `skills/mcp-builder/SKILL.md`

- Skill page: [anthropics-skills-skills-mcp-builder](../skills/by-category/agent-infrastructure-skill-creation/official-reference/anthropics-skills-skills-mcp-builder.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/official-reference/anthropics-skills-skills-mcp-builder`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/official-reference/anthropics-skills-skills-mcp-builder/SKILL.md`
- Source: [anthropics/skills `skills/mcp-builder/SKILL.md`](https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/mcp-builder/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `2c7ec5e78b8e`
- What it covers: Catalog summary: Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. Use when building MCP servers to integrate external APIs or services, whether in Python (FastMCP) or Node/TypeScript (MCP SDK).
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: MCP Server Development Guide, Overview, Process, 🚀 High-Level Workflow, Phase 1: Deep Research and Planning. Resources: has_scripts.
- Notability: Included from official skill reference with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-anthropics-skills-skills-mcp-builder-skill-md`: Use the immutable source file https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/mcp-builder/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## token-integration-analyzer - trailofbits/skills `plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md`

- Skill page: [trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer](../skills/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer/SKILL.md`
- Source: [trailofbits/skills `plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Token integration and implementation analyzer based on Trail of Bits' token integration checklist. Analyzes token implementations for ERC20/ERC721 conformity, checks for 20+ weird token patterns, assesses contract composition and owner privileges, performs on-chain scarcity analysis, and evaluates how protocols handle non-standard tokens. Context-aware for both token implementations and token integrations.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Token Integration Analyzer, Purpose, How This Works, Phase 1: Context Discovery, Phase 2: Slither Analysis (if Solidity). Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

## skill-improver - trailofbits/skills `plugins/skill-improver/skills/skill-improver/SKILL.md`

- Skill page: [trailofbits-skills-plugins-skill-improver-skills-skill-improver](../skills/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-skill-improver-skills-skill-improver.md)
- Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-skill-improver-skills-skill-improver`
- Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/security-reference/trailofbits-skills-plugins-skill-improver-skills-skill-improver/SKILL.md`
- Source: [trailofbits/skills `plugins/skill-improver/skills/skill-improver/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/skill-improver/skills/skill-improver/SKILL.md)
- Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`
- What it covers: Catalog summary: Iteratively reviews and fixes Claude Code skill quality issues until they meet standards. Runs automated fix-review cycles using the skill-reviewer agent. Use to fix skill quality issues, improve skill descriptions, run automated skill review loops, or iteratively refine a skill. Triggers on 'fix my skill', 'improve skill quality', 'skill improvement loop'. NOT for one-time reviews—use /skill-reviewer directly.
- Agent use: Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.
- Observed structure: Headings: Skill Improvement Methodology, Prerequisites, Core Loop, When to Use, When NOT to Use. Resources: none observed.
- Notability: Included from security and audit skills with explicit GitHub provenance.
- Improvement and correction plan:
  - Keep provenance and selected ref visible so agents can verify the source before use.
  - Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
  - Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Assigned benchmark scenarios:
  - `skill-proof-trailofbits-skills-plugins-skill-improver-skills-skill-improver-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/skill-improver/skills/skill-improver/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
  - `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
  - `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
  - `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.
