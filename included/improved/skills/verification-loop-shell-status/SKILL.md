---
name: verification-loop-shell-status
description: Verify a substantial change with the project's declared commands. Preserve actual failure status, source identity, test scope and evidence that affected callers work.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  revision-status: experimental-unbenchmarked
---

# Verify a change

Read the repository instructions, manifests and relevant CI. Identify the
requested behavior, affected callers, supported environments and required checks.
Resolve the intended base from live source control. Preserve unrelated changes.

## Choose checks that expose the defect

- Define observable outcomes, boundaries and plausible wrong results. For a
  bug, reproduce the failure when practical and keep the focused case after
  the repair.
- Use the project's declared runner, dependencies, commands and configuration.
  Start with the affected behavior, then cover direct consumers and required
  broader gates. For runtime claims, verify the built or installed artifact
  those consumers use. Separate syntax checks, focused behavior and full-scope
  verification.
- Follow the project's coverage policy and inspect unexercised behavior.
  Qualify tests through their real assertions and case reports. A reported
  coverage percentage alone leaves assertion correctness unresolved.

## Preserve actual results

Run the required executable with the intended arguments. Capture its complete
bounded output and exit status before showing excerpts. For a shell pipeline
or output wrapper, [verify argument and exit propagation](references/native-command-status.md).
Check that callers receive the return status, structured payload and failure
diagnostic they depend on.

Record the command, tool/runtime, input revision, intended case IDs, outcome and
retained evidence. Confirm the failure phase and actual diagnostic. Distinguish
assertion failures from setup, timeouts, aborts, skips and unavailable checks.
Retain the first failure when a corrected invocation later passes. Retry when
evidence identifies a transient failure or an input to correct.

## Check and report the delivered scope

Review staged and unstaged changes, generated outputs and relevant untracked
files. Validate source identities and rerun affected checks after input changes.
Keep required gates visible, honor authorized scope, and verify hosted results
against the delivered commit. Keep credential-bearing logs private.

Lead with the resulting behavior. State which commands ran, their outcomes and
the unverified scope. Claim completion when the acceptance criteria and
required gates have evidence.
