# Click development-task calibration

The [Windows result](windows.json) and [Linux result](linux.json) were produced
by the [calibration tool](../../../../benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/README.md)
against the same 142-file source snapshot and task inputs. Windows used
CPython 3.14.10; Linux used CPython 3.14.8 under WSL. In each run, the original
failed 12 of 16 cases, the upstream fix and an alternative passed all 16, and
the three intentionally incomplete variants failed their expected cases.

These are trusted source-variant controls, not agent trials. The local raw
stdout and stderr were retained in the ignored research workspace, and their
hashes are recorded in the result files; they are not included here because
failure tracebacks contain host-specific paths. The hosted workflow uploads its
own raw outputs. The result files do not by themselves independently prove
that the commands ran, and the tests do not exercise an interactive terminal.
