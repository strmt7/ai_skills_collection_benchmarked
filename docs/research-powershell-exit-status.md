# PowerShell exit-status controls

The experimental [verification overlay](../included/improved/skills/verification-loop-shell-status/SKILL.md)
now distinguishes the status of a native producer from the status left by a
later native command. This review covers shell status handling only; it does not
establish that the overlay improves a coding agent.

## Source comparison

The catalog mirror is pinned to `affaan-m/everything-claude-code` commit
`846ffb75da9a5f4e677d927af1ad4a1951652267`. On 3 November 2026 GitHub reported
`v2.2.3` as the latest stable release. Its annotated tag resolves to commit
`c05b2d6614f62f6db0047669aa4eefb223d478f9`; the release's
[verification-loop file](https://github.com/affaan-m/everything-claude-code/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/verification-loop/SKILL.md)
has Git blob `b936bc9646e3b286dbe89ab2b2a7fb47bf3ad28e` and SHA-256
`6d4a399d856207297168cc03f3f8c90d4085ff14566bb928af3c97d9a31f2650`.
The file body matches the locked mirror after newline normalization; its
frontmatter differs. This is a one-file comparison, not an assessment of the
complete release.

## Observed behavior

On Windows, the [control](../benchmarks/dependency-regressions/verification_powershell.py)
ran six cases each in Windows PowerShell 5.1.26100.9818 and PowerShell 7.6.5,
using Python 3.13.17 as a known native producer and consumer. The
[recorded results](../artifacts/research/2026-11-03/verification-powershell-status-v1/result.json)
bind the outcomes to the control source.

| Case | Observed in both hosts |
| --- | --- |
| Producer run directly | Exited 7 after writing `payload`. |
| Failing producer piped to a successful native consumer | The wrapper observed `$LASTEXITCODE` 0. |
| Failing native command piped to a PowerShell cmdlet | `$LASTEXITCODE` remained 7 in this case. |
| Producer run separately, status saved, then output inspected | The wrapper propagated the saved status 7 even after another successful native command. |
| `$ErrorActionPreference = 'Stop'`, with native-command preference disabled | Execution continued after the nonzero native exit. |
| Failed cmdlet after a native exit of 7 | The cmdlet's `$?` was false while `$LASTEXITCODE` still held 7. |

These cases do not characterize every pipeline, shell configuration or native
application. In particular, PowerShell's native-command preference changes
error handling when enabled. Microsoft's documentation distinguishes
[`$LASTEXITCODE` and `$?`](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables?view=powershell-7.6#lastexitcode)
and describes [native command error handling](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_error_handling?view=powershell-7.6#external-program-errors).

The first independent harness incorrectly quoted a Python argument for Windows
PowerShell 5.1: the producer raised `NameError` instead of exiting 7. That
attempt was not accepted as evidence of the intended case. The corrected fixture
uses a quoting-independent producer; direct execution confirms its status before
the pipeline comparison. A separate negative check changed the expected pipeline
status to 7 and correctly rejected both host runs.

Run the Windows controls with a new output path:

```powershell
python benchmarks/dependency-regressions/verification_powershell.py --output "$env:TEMP/verification-powershell-result.json"
```

Choose a different path if that file already exists. The following check runs on
any supported Python host and checks the recorded cases and control-source hash;
it does not rerun PowerShell:

```sh
python benchmarks/dependency-regressions/verification_powershell.py --output artifacts/research/2026-11-03/verification-powershell-status-v1/result.json --check
```

The earlier [experimental overlay](../included/improved/skills/verification-loop-current/SKILL.md)
and its historical manifest remain unchanged. The current overlay remains
experimental and has not been evaluated in an independent matched agent trial.
