# SkillsBench SimPO development-task review

This review concerns the public development task
[`simpo-code-reproduction`](https://github.com/benchflow-ai/skillsbench/tree/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/simpo-code-reproduction)
at the task commit pinned by SkillsBench v1.1. Its
[verifier](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/simpo-code-reproduction/verifier/test_outputs.py)
loads the submitted output before deleting it and invoking the test program.
After the invocation, it checks the new file's existence and modification time,
but compares data through the earlier loaded archive instead of reloading the
new file.

A controlled call to the unmodified verifier on Linux accepted a correct
initial file followed by a regenerated file with incorrect loss values. It also
accepted a regenerated archive with a different key. It rejected an incorrect
initial file, a missing regenerated file and a simulated failing subprocess.
The correct initial and regenerated outputs were accepted. The control uses the
pinned reference archive and simulates the subprocess and environment-info
file; it does not run the supplied unit test or SimPO training.

The [reproducer](../artifacts/research/2026-10-30/skillsbench-simpo-regeneration/reproduce.py)
checks both source hashes and routes the fixed paths to temporary files. The
[Python 3.10 result](../artifacts/research/2026-10-30/skillsbench-simpo-regeneration/linux-py310-result.json)
uses NumPy 1.24.2, the version named in the upstream test wrapper; the
[Python 3.12 result](../artifacts/research/2026-10-30/skillsbench-simpo-regeneration/linux-py312-result.json)
uses NumPy 2.4.4. Both show the same controlled outcomes. The experiment
rejected altered source bytes and optimized Python mode. Run `--help` for the
required pinned verifier and reference files.

This is a component finding, not a full task or harness run, and it does not
score a model. It does not establish how often a real submission produces a
wrong regenerated archive. No held-out task content was read. Preserve the
upstream verifier and define any corrected post-run comparison in a distinct,
predeclared evaluation protocol.

## Separate snapshot comparison control

The [post-run comparison control](../benchmarks/component-controls/simpo-postrun/compare.py)
compares supplied archive bytes with the pinned public reference. It checks the
reference digest and requires one finite, real floating-point loss vector of
exactly 100 elements. It rejects a wrong key, broadcastable wrong shape,
nonfinite values, and values outside tolerance. Missing input or an invalid
reference yields an unavailable result rather than a score. The component
checks and their [recorded results](../artifacts/research/2026-11-02/simpo-postrun-comparison/qualification.json)
use synthetic archives and the public development-task reference.

The tolerance values match the upstream task (`rtol=1e-5`, `atol=1e-6`),
but this comparison deliberately puts the reference on the right-hand side of
`numpy.allclose`; the upstream initial comparison uses the generated values on
that side. Relative tolerance is asymmetric, so this is a distinct rule, not
an equivalent implementation of the original verifier. See the
[NumPy allclose documentation](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html).

This control does not generate the archive, establish its freshness, execute
the upstream program or harness, validate the reference's scientific
correctness, or measure agent performance. It is not integrated into a model
trial. This public task is development-exposed and is not a held-out test.
To exercise the control with a separately obtained pinned reference archive:

```sh
python benchmarks/component-controls/simpo-postrun/reproduce.py --reference path/to/loss.npz
```

The separate [development-task candidate](../benchmarks/agent-effectiveness/development/simpo-verifier-v1/TASK.md)
uses the original verifier as a coding fixture and calibrates its acceptance
cases against the unmodified verifier and two reference repairs. Its subprocess
is simulated and the task is already exposed; it is not a model score or a
qualified grader for agent submissions.
