# market-research

Category: Finance, commerce & forecasting

Mirrored skill: `included/skills/by-category/finance-commerce-forecasting/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-market-research`

Agent-ready entrypoint: `included/agent-ready/by-category/finance-commerce-forecasting/selected-structure-reference/affaan-m-everything-claude-code-agents-skills-market-research/SKILL.md`

Source: [affaan-m/everything-claude-code `.agents/skills/market-research/SKILL.md`](https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/market-research/SKILL.md)

Selected ref: `v1.10.0`; commit `846ffb75da9a`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Conduct market research, competitive analysis, investor due diligence, and industry intelligence with source attribution and decision-oriented summaries. Use when the user wants market sizing, competitor comparisons, fund research, technology scans, or research that informs business decisions.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-affaan-m-everything-claude-code-agents-skills-market-research-skill-md`: Use the immutable source file https://github.com/affaan-m/everything-claude-code/blob/846ffb75da9a5f4e677d927af1ad4a1951652267/.agents/skills/market-research/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `finance-commerce-and-forecasting-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.
- `finance-commerce-and-forecasting-nyc-tlc-trip-records`: Clean, aggregate, and explain large real trip data.
- `finance-commerce-and-forecasting-stackoverflow-survey`: Analyze survey data and produce reproducible charts.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
