---
name: workflow-call-inputs
description: Define and validate typed inputs for GitHub Actions reusable workflows, including when a manually dispatched workflow offers choice or environment inputs.
license: Apache-2.0
metadata:
  source: akin-ozer/cc-devops-skills
  source-commit: 7fe7595e4512f8ce43dcf956aa5190b96d627dd1
  revision-status: experimental-unbenchmarked
---

# Reusable workflow input types

Apply the [mandatory agent-tool policy](../../../../docs/agent-tools.md) and
the current project's workflow instructions. This adaptation addresses input
types only; it does not qualify the source generator's other templates.

For `on.workflow_call.inputs`, GitHub requires each input's type to be
`boolean`, `number`, or `string`. Use a value matching the declared type for
an optional default. Here is a complete reusable workflow:

```yaml
name: Reusable input example
on:
  workflow_call:
    inputs:
      target:
        type: string
        required: true
      repetitions:
        type: number
        default: 2
      verbose:
        type: boolean
        default: false
jobs:
  show:
    runs-on: ubuntu-latest
    steps:
      - name: Show inputs
        env:
          TARGET: ${{ inputs.target }}
          REPETITIONS: ${{ inputs.repetitions }}
          VERBOSE: ${{ inputs.verbose }}
        run: printf 'target=%s repetitions=%s verbose=%s\n' "$TARGET" "$REPETITIONS" "$VERBOSE"
```

`workflow_dispatch` additionally supports `choice` and `environment` inputs;
those are not valid `workflow_call` input types. If a reusable workflow needs
one of those values, receive it as a string and check any allowed-value or
environment requirements appropriate to that workflow. Do not assume a
manual selection alone configures the called job's environment.

Check both the caller and the called workflow, including default values and
expressions. Validate the generated files with the project's available GitHub
Actions tooling and review current GitHub documentation. Static linting can
catch invalid definitions; it does not prove that a hosted run will succeed.
The [component controls](../../../../docs/research-workflow-call-inputs.md)
cover selected definitions and have not measured agent effectiveness.
