# Development task: verify the regenerated result

This candidate task adapts a public SkillsBench development verifier. It is
already exposed, including its acceptance controls and reference solutions.
It is not a holdout, an agent run, or a qualified scoring integration.

## Task brief

The provided `test_outputs.py` checks a submitted loss archive, removes it,
runs the supplied SimPO unit test, and checks the regenerated archive. Fix it
so that it validates the actual archive produced by that run. Preserve the
initial archive, environment-version, subprocess-success and freshness checks.
Release file handles before deleting or replacing the output.

Both initial and regenerated output must have a `losses` array matching the
reference array's shape, with finite values. A missing `losses` key must fail
validation. Compare values using `numpy.allclose(reference, output, rtol=1e-5,
atol=1e-6)`; do not permit broadcasting to turn different shapes into a pass.
The unit-test invocation, working directory, `PYTHONPATH`, and captured
process output remain part of the existing workflow.

## Design scope

The fixture is the exact public verifier at the source commit recorded in
`source.json`; the unchanged upstream file and its Apache-2.0 license are
preserved. The acceptance cases were specified from this task's behavior, not
from any skill being evaluated. The controls use synthetic arrays and simulate
the unit-test subprocess, paths, and freshness. They test two valid controls
with different path and import styles, not every valid implementation or a live SimPO run.
Their path and subprocess shims do not establish grading isolation.

The [recorded calibration](../../../../artifacts/research/2026-11-02/simpo-verifier-task-calibration/)
contains source-bound Windows and Linux results. To reproduce it, create a
Python 3.13 environment and install the appropriate hash-locked Linux or
Windows requirements from `benchmarks/component-controls/simpo-postrun/`.
Then run:

```sh
python benchmarks/agent-effectiveness/development/simpo-verifier-v1/controls/calibrate.py --output /new/output-directory
```

The original verifier control runs only on Linux, its upstream environment.
Both reference controls run on either platform. Raw pytest output and JUnit
files are retained in the requested output directory.

Do not use these host-executed calibration controls to grade an agent
submission. A counted model trial still requires a separately qualified
confined grader, a frozen protocol and manifest, and the other safeguards in
[the trial protocol](../../../../docs/agent-trial-protocol.md). Future agent
workspaces must not include these reference solutions or evaluator controls.
