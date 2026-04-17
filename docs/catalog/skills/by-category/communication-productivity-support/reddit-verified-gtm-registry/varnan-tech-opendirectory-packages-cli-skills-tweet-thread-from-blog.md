# tweet-thread-from-blog

Category: Communication, productivity & support

Mirrored skill: `included/skills/by-category/communication-productivity-support/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-tweet-thread-from-blog`

Agent-ready entrypoint: `included/agent-ready/by-category/communication-productivity-support/reddit-verified-gtm-registry/varnan-tech-opendirectory-packages-cli-skills-tweet-thread-from-blog/SKILL.md`

Source: [Varnan-Tech/opendirectory `packages/cli/skills/tweet-thread-from-blog/SKILL.md`](https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/tweet-thread-from-blog/SKILL.md)

Selected ref: `default-branch HEAD`; commit `bc01f7c1c31f`

## Use

Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.

## Scope

Catalog summary: Converts a blog post URL or article into a Twitter/X thread with a strong hook, one insight per tweet, and a CTA. Optionally posts the full thread to X via Composio using a reply chain. Use when asked to turn a blog post into a tweet thread, repurpose an article for Twitter, create a thread from a blog, write a Twitter thread about a topic, or share a blog post as a thread. Trigger when a user mentions Twitter.

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-varnan-tech-opendirectory-packages-cli-skills-tweet-thread-from-blog-skill-md`: Use the immutable source file https://github.com/Varnan-Tech/opendirectory/blob/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/tweet-thread-from-blog/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `communication-productivity-and-support-enron-email`: Classify, summarize, and route real email threads.
- `communication-productivity-and-support-ms-marco`: Rank passages and support answer extraction.
- `communication-productivity-and-support-sec-edgar-companyfacts`: Extract and reconcile financial facts from filings.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.
