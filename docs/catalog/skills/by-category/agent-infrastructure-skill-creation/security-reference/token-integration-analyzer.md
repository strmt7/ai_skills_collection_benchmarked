# token-integration-analyzer

Category: Agent infrastructure & skill creation

Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/security-reference/token-integration-analyzer`

Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/security-reference/token-integration-analyzer/SKILL.md`

Source: [trailofbits/skills `plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md`](https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md)

Selected ref: `default-branch HEAD`; commit `e8cc5baf9329`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Token integration and implementation analyzer based on Trail of Bits' token integration checklist. Analyzes token implementations for ERC20/ERC721 conformity, checks for 20+ weird token patterns, assesses contract composition and owner privileges, performs on-chain scarcity analysis, and evaluates how protocols handle non-standard tokens. Context-aware for both token implementations and token integrations.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-trailofbits-skills-plugins-building-secure-contracts-skills-token-integration-analyzer-skill-md`: Use the immutable source file https://github.com/trailofbits/skills/blob/e8cc5baf9329ccb491bfa200e82eacbac83b1ead/plugins/building-secure-contracts/skills/token-integration-analyzer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
