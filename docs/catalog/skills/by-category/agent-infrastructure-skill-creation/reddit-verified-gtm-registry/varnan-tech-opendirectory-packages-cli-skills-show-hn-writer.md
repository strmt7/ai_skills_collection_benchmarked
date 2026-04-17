# show-hn-writer

Category: Agent infrastructure & skill creation

Mirrored skill: `included/skills/by-category/agent-infrastructure-skill-creation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer`

Agent-ready entrypoint: `included/agent-ready/by-category/agent-infrastructure-skill-creation/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-show-hn-writer/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/show-hn-writer/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/show-hn-writer/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Use for show-hn-writer workflows. Source sections include Show HN Writer, Step 1: Gather Project Context, Step 2: Read Context Files (if available).

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-show-hn-writer-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/show-hn-writer/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `agent-infrastructure-and-skill-creation-beir-retrieval`: Evaluate retrieval workflows across datasets.
- `agent-infrastructure-and-skill-creation-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `agent-infrastructure-and-skill-creation-common-crawl-warc`: Retrieve, parse, and cite web-scale documents.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
