---
name: azure-pipelines-sequence-preflight
description: Check literal Azure Pipelines stage, job and step sequence shapes before service validation.
license: Apache-2.0
---

# Azure Pipelines sequence preflight

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

This optional preflight inspects literal sequence-entry shapes in top-level
`stages`, `jobs` and `steps` and statically visible nested jobs and steps.
Install the pinned dependencies in an isolated Python environment with
`python -m pip install --require-hashes -r requirements.txt`, then run
`python preflight.py path/to/azure-pipelines.yml --json` from this directory.

Exit 0 (`no_shape_issues`) means only that no shape issue was identified in the
checked subset. Exit 1 (`issues`) reports at least one malformed literal shape;
exit 2 (`indeterminate`) reports unresolved forms such as templates; exit 3
(`invalid_input`) reports unreadable or malformed input. Diagnostics include
locations where applicable. The JSON field `azure_schema_validated` is always
false. If issues and unresolved forms coexist, exit 1 retains both lists.

This tool does not expand templates or validate the Azure schema, task versions,
expressions, pipeline behavior, deployment jobs or the complete source skill.
For example, `task: ExampleTask` receives no shape issue although the original
syntax validator flags its missing version. Use the intended Azure DevOps
service to validate and run the pipeline before relying on it. Treat unresolved
forms as requiring service validation, not as errors or passes.

The original instructions and syntax component are retained in `provenance/`.
The component controls do not prove agent effectiveness or Azure service behavior.
