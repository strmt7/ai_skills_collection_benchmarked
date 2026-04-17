# verification-loop

Category: Testing, QA & benchmarking

Mirrored skill: `included/skills/by-category/testing-qa-benchmarking/selected-project-reference/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop`

Agent-ready entrypoint: `included/agent-ready/by-category/testing-qa-benchmarking/selected-project-reference/strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop/SKILL.md`

Source: [strmt7/simple_ai_bitcoin_trading_binance `.agents/skills/verification-loop/SKILL.md`](https://github.com/strmt7/simple_ai_bitcoin_trading_binance/blob/451d77df90621e3b666581d9835d246fb7147349/.agents/skills/verification-loop/SKILL.md)

Selected ref: `default-branch HEAD`; commit `451d77df9062`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Use for verification-loop workflows. Source sections include Verification Loop, Principle, Process.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-strmt7-simple-ai-bitcoin-trading-binance-agents-skills-verification-loop-skill-md`: Use the immutable source file https://github.com/strmt7/simple_ai_bitcoin_trading_binance/blob/451d77df90621e3b666581d9835d246fb7147349/.agents/skills/verification-loop/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `testing-qa-and-benchmarking-swe-bench-lite`: Patch real GitHub issue tasks and verify with repository tests.
- `testing-qa-and-benchmarking-owasp-benchmark`: Find and classify vulnerability test cases.
- `testing-qa-and-benchmarking-local-omero-compose-workflows`: Validate OMERO deployment, plugin, upload/import, and monitoring workflows.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
- Add an executable validator or helper script so the workflow has objective checks.
