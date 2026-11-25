# Native command status

A pipeline can return success when a producer failed and a later command
completed. Capture the executable's exit code with a supported shell mechanism
or run it through the language's process API with an argument vector.

- On POSIX shells, pipeline status ordinarily comes from the last process.
  Choose the shell's supported producer-status mechanism or capture the
  command output first. Then show excerpts without changing its status.
- In PowerShell, invoke a path with `& $executable`. Save `$LASTEXITCODE`
  immediately after the native command and propagate that value when wrapping
  the call. Track cmdlet failures through PowerShell's error behavior. The
  effect of `$ErrorActionPreference` on native commands depends on the host
  and its native-command preference.
- When exact argument boundaries matter, particularly an empty argument in
  Windows PowerShell 5.1, use a process API with a declared argument vector
  and check received arguments in a control.

Exercise each supported entrypoint with a successful payload and a failure.
Include redirection, assignment or pipelines when callers rely on them.
Verify that each caller gets usable output, the expected failure diagnostic
and the original exit status. Check exact output bytes when a consumer
requires them.
