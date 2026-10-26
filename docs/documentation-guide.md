# Write documentation users can act on

Write for the person trying to use the collection. Lead with their task, explain
the needed requirements and show the expected outcome. Keep implementation and
contributor procedures in the linked development guide. Use plain language,
short examples and precise evidence labels.

## Structure

The public entrypoints lead to installation, choosing a skill, using it and
interpreting its results. Reference pages hold exact configuration and source
facts. Explanations describe evidence and tradeoffs. Contributor setup, execution
policy, release procedures and reproducibility belong in
[CONTRIBUTING](../CONTRIBUTING.md) and [development setup](development.md).
Link those guides at the bottom of user-facing entrypoints.

This separates learning, task instructions, reference and explanation as
described by [Diátaxis](https://diataxis.fr/start-here/). Audience and vocabulary
choices follow [Google's audience guidance](https://developers.google.com/tech-writing/one/audience).
These are design choices supported by the sample below, not a claim that all
enterprise repositories use one layout.

## Reviewed project patterns

| Project | Observed user entrypoint | Contribution and policy placement |
| --- | --- | --- |
| [Ruff](https://github.com/astral-sh/ruff/blob/e139fbd6e8ddd5a1653d2f2c15c1123c090a3456/README.md) | Installation, usage and configuration examples | Separate contribution guide; CI has explicit permissions, cancellation and distinct validation jobs |
| [pytest](https://github.com/pytest-dev/pytest/blob/082ed70e314ee8e1ab117763d17fe801648f7508/README.rst) | A small test and its actual failure output, then documentation links | Contribution and security files; separate link checking and test workflow |
| [VS Code](https://github.com/microsoft/vscode/blob/af3b54ddd0c4f81765fc218856e2e73491051092/README.md) | Product purpose, download and feedback routes | Build and development workflow linked separately; CI separates change selection, tests and final gate |
| [Kubernetes](https://github.com/kubernetes/kubernetes/blob/623dec64e7cffd0b273d9c0664a611de433b8f10/README.md) | Using the product precedes developing it | Contributor guide and security reporting linked separately; no in-repository GitHub Actions workflow was found in this captured tree |
| [Agent Skills](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/README.md) | Format, discovery, activation and getting started | Separate contributor document with concrete evidence and AI-disclosure rules |
| [Anthropic skills](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/README.md) | Skill purpose, sets and client-specific use | Explicit distinction between demonstration, production behaviour and differing licences |

The corresponding public documentation pages reinforce task-based navigation:
[Ruff](https://docs.astral.sh/ruff/),
[pytest](https://docs.pytest.org/en/stable/getting-started.html),
[VS Code](https://code.visualstudio.com/docs) and
[Kubernetes](https://kubernetes.io/docs/home/). The survey inspected README
entrypoints and selected policy/workflow properties, not every source file or
all of these projects' external CI systems. Popularity informed the sample;
it is not evidence of operational quality or a benchmark ranking.

## Evidence and maintenance

Keep a single current readiness page. Historical progress remains accessible in
Git history; do not present an old checkpoint as current status. Preserve
frozen benchmark inputs, failed runs, licence notices and evidence hashes.
Generated catalog pages must be changed through their generator.

Distinguish a planned check, a passing component check and a measured model
result. Name the tested source, runtime and scope. Do not infer commercial
readiness from a badge. Do not add universal coverage targets to create a green
status or copy a larger project's workflow complexity without a relevant need.

For coverage, [Codecov's action](https://github.com/codecov/codecov-action/blob/303a32d7a59b442fa8d48b6a1cc6825c09c847a5/README.md#using-oidc)
defines OIDC authentication and
[its YAML guide](https://docs.codecov.com/docs/codecov-yaml) defines repository
configuration and validation. The read-only FlitzZip reference supplied the
badge shape and measured-report workflow; this collection uses its own Python
coverage scope. No owner repository was changed.

Source revisions, native Git blob hashes, selected workflow properties and
Crawl4AI receipt metadata are retained in
[the survey record](../artifacts/research/documentation/enterprise-survey.json).
