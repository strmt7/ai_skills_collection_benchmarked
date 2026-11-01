# Anthropic API skill: model and upstream review

The catalog's [pinned Anthropic API skill](../included/skills/by-category/coding-refactoring-repository-automation/official-reference/claude-api-anthropics/SKILL.md)
defaults to `claude-opus-4-7` and contains a model table dated 15 April 2026.
On 1 November 2026, Anthropic's [model overview](https://platform.claude.com/docs/en/models/overview)
listed a newer lineup and recommended Opus 5.5 for most workloads. Its
[model lifecycle page](https://platform.claude.com/docs/en/about-claude/model-deprecations)
still listed Opus 4.7 as active. The pinned choice is therefore older guidance;
it is not documented here as retired.

Anthropic's [prompt-caching documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
says minimum cacheable prefix lengths depend on the model, and shorter prefixes
are processed without caching. The presence of a cache option alone is not
evidence of a cache hit. For a real integration, verify the current model ID,
availability, price, request format and cache usage against the target provider
and workload. Preserve a user's explicit model choice unless a change is requested.

The [source comparison](../artifacts/research/2026-11-01/anthropic-claude-api-source-observation.json)
examined the `skills/claude-api/` tree at the catalog's pinned commit and at
upstream commit `ca45fc496a3436251f191354091d557da31c15b5`. It found 40 pinned
files and 96 current files: 61 added, five removed and 35 changed. This includes
changes to the skill and its license file. Those counts are source-tree
observations, not a review or approval of every changed file. The locked mirror
remains unchanged; adopting the upstream update requires reviewing and
regenerating the affected locked source set.

No Anthropic API request, application integration, cost measurement or agent
benchmark was run in this review. Model availability and pricing can change;
consult the linked provider documentation before use.
