# Validate a native build result

Build outcomes must agree with the declared command, native execution and the
original benchmark scorer. The validator preserves valid failures and timeouts
as scored failures. Inconsistent or incomplete evidence is unscored.

Validate the included native compilation control:

```powershell
$control = 'artifacts/research/2026-11-13/publisher-build-scorer/native/compiled-source'
./dev.ps1 python tools/verify_swe_skills_bench_build_result.py `
  --inventory "$control/inventory.json" --execution "$control/execution.json" `
  --publisher "$control/publisher.json" --stdout "$control/stdout.native" `
  --stderr "$control/stderr.native" --json
```

Use `python` in place of `./dev.ps1 python` in an existing supported environment.
The validator itself requires no container engine or model account. Native
execution needs a separately qualified controller and runtime.

The five input files contain:

| Input | Required evidence |
|---|---|
| Inventory | Task ID, original build command, `/workspace` working directory, expected exit code and timeout |
| Execution | Exact invoked command and timeout, exit code, timeout flag, duration, output digests, completed transport and zero remaining owned processes |
| Publisher | Unmodified L1 `build_check` result, matching native outcome and associated command details |
| Standard output/error | Original bytes matching the execution digests |

JSON envelopes use schema version 1. A valid result returns `admitted: true`
and either `task_passed` or `task_failed`; both return CLI exit code 0.
Invalid evidence returns `unscored`, omits the score and returns exit code 1.
Do not interpret validator exit code 0 as a successful project build.

The [qualification review](../artifacts/research/2026-11-13/publisher-build-scorer/review.json)
retains native compilation, syntax failure, declared nonzero exit, diagnostic
text, timeout and command-mismatch controls against the original publisher
implementation. Diagnostic text does not replace its exit-code metric.

The validator checks evidence consistency. It cannot authenticate the producer
or prove that an arbitrary caller executed a build. Counted trials also need
qualified execution, collection, provenance and model boundaries. Complete
build-stage integration, all selected project dependencies and the original
multi-stage aggregate remain open; these controls are not model benchmark scores.
