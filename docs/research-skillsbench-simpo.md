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
