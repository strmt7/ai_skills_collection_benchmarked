# Pytest skipped-class development control

This public task adapts a real pytest issue. It starts from a complete pinned
checkout and tests copies of its `src` tree. The controls, source patch and
issue are public development material, not an untouched holdout. The
[task brief](TASK.md) describes the behavior; [source.json](source.json)
records the Git commit, original MIT license, upstream patch and source
observations. The patch is stored as UTF-8 text in a JSON transport; its
decoded bytes are checked against the recorded upstream digest.

The 25 subprocess controls are independent of skill text and cover class,
inherited and method skips, conditional `unittest` decorators, pytest skip
markers, ordinary test lifecycles, and debugger-before-teardown ordering.
Calibration expects the original checkout to fail six cases, the upstream patch
and a separately expressed alternative to pass all cases, and three deliberately
incorrect variants to fail their relevant cases. These are limited test examples, not a
proof that every correct implementation passes. The issue, Python documentation
and upstream pytest tests informed the cases. No model is invoked or scored.
The [recorded calibration](../../../../artifacts/research/2026-11-02/pytest-pdb-task-calibration/qualification.json)
binds both platform runs to their inputs and retains the upstream-test observations.

Five of the public issue's upstream tests were also run separately on Windows and
Linux with Python 3.11: the original failed one and passed four related cases;
the upstream fix passed all five. This was not the full upstream test suite.
A Python 3.12 attempt failed during
collection because this historical pytest source uses deprecated AST APIs.
That failed setup is not a model or task outcome.

## Reproduce the controls

The [workflow](../../../../.github/workflows/pytest-pdb-task.yml) demonstrates
the complete Windows/Linux setup. It fetches the pinned commit and version
history, creates an isolated Python 3.11.18 environment, installs the
platform-specific hash-locked runtime graph, and installs the checkout in that
environment using the recorded build constraints. Use a clean full checkout;
the normal editable installation generates pytest's version metadata.

Then, with the environment active, run the control with a **new output
directory outside the source checkout**:

```sh
python benchmarks/agent-effectiveness/development/pytest-unittest-pdb-skip-v1/controls/calibrate.py \
  --source /path/to/pinned/pytest-checkout \
  --target-python /path/to/venv/python \
  --output /path/to/new/calibration-output
```

On Windows, use the venv's `Scripts/python.exe` as `--target-python`. The
output contains each trusted variant's raw stdout and stderr plus a JSON
result binding the task inputs, runtime, source snapshot and observations.
Existing output directories are rejected. The runner copies source into a
temporary workspace and verifies that its source inputs remain unchanged.

Do not use these host-executed controls to grade agent-generated code. A
counted trial requires separately qualified execution and grading, a frozen
protocol, and an independent case manifest. See the
[agent-trial protocol](../../../../docs/agent-trial-protocol.md).
