# browser-act

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/browser-automation-reference/browser-act-skills-browser-act`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/browser-automation-reference/browser-act-skills-browser-act/SKILL.md`

Source: [browser-act/skills `browser-act/SKILL.md`](https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/browser-act/SKILL.md)

Selected ref: `default-branch HEAD`; commit `749ed52133b8`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Browser automation CLI for AI agents with anti-detection stealth browsing, captcha solving, and parallel multi-browser support. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, scraping sites with bot detection, or automating any browser task. Also use when the user needs to connect to their existing Chrome session,.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-browser-act-skills-browser-act-skill-md`: Use the immutable source file https://github.com/browser-act/skills/blob/749ed52133b85606cf402b7fda95949542cbb8f8/browser-act/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
