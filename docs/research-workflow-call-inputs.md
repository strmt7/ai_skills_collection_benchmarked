# Reusable workflow input-type review

The pinned GitHub Actions generator's reusable-workflow template lists
`choice` and `environment` alongside `string`, `boolean`, and `number` under
`workflow_call.inputs`. The [GitHub workflow syntax reference](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_callinputsinput_idtype)
allows only `boolean`, `number`, and `string` for `workflow_call` inputs.
`choice` and `environment` are additional types for
[`workflow_dispatch` inputs](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#onworkflow_dispatchinputsinput_idtype).

The experimental [workflow-call-inputs skill](../included/improved/skills/workflow-call-inputs/SKILL.md)
provides a typed reusable-workflow example. The source skill and reusable
template are preserved in the overlay's provenance directory; the catalog
mirror is unchanged. This is a narrow correction, not a review of the whole
generator or a claim about agent performance.

The independent component controls exercise all five candidate types under
each event, selected matching and mismatching default values, and the maintained
example with actionlint. The expected type sets were defined from GitHub's
reference independently of the skill text.
On 2 November 2026, actionlint 1.7.12 produced the expected results for all 16
cases on Windows with Python 3.13.17 and Linux with Python 3.12.3. The
[qualification record](../artifacts/research/2026-11-02/workflow-call-inputs/qualification.json)
binds the outcomes to the source, overlay, control and executable hashes. Local
native results remain in independent host evidence; the
[workflow](../.github/workflows/workflow-call-inputs.yml) uploads new results.

Actionlint is a static checker, not a GitHub-hosted execution of the generated
example; successful linting does not establish that a workflow runs correctly
or that an agent will select or use the skill.
