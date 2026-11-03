# Click prompt suffix development task

This is an exposed development candidate based on a real Click issue. The
[task brief](TASK.md) and [source record](source.json) identify the pinned
revision, license, source tree and upstream fix. The 16 independent behavioral
controls check both prompt APIs, empty and nonempty suffixes, Unicode,
defaults and retries. They do not exercise a real interactive terminal or
prove the readline workaround works in every environment.

The calibration runs the original source, the exact upstream patch, a
separately expressed alternative and three deliberately incomplete changes.
It verifies every extracted source file against the 142 Git blobs recorded in
`tree.json`, checks the fixed module's SHA-256, and retains each process's raw
output and case outcomes. Its manifest records file modes, but calibration
checks file contents and paths, not filesystem mode bits. The patch is a
GitHub API source-file patch with standard diff headers added and stored in a
UTF-8 JSON transport; the decoded bytes and resulting source are checked against
the recorded digests. This is not a model benchmark.

The [local calibration records](../../../../artifacts/research/2026-11-03/click-prompt-task-calibration/)
bind the same source snapshot and control inputs on Windows and Linux. The
original fails 12 cases, the upstream patch and alternative pass all 16, and
each incomplete variant fails its expected cases. Raw local logs remain in the
research workspace; the hosted workflow retains its own raw outputs. These
controls do not establish task difficulty or compare coding agents.

Obtain and extract the public archive identified in `source.json` into a new
directory. Run the following from the collection root with CPython 3.11 or later
and Git installed, replacing both paths. The output must be a new directory
outside the extracted source tree.

```sh
python benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/controls/calibrate.py \
  --source /path/to/extracted-click-source \
  --output /path/to/new-calibration-output
```

Use `--target-python` to select the interpreter running the controls. Source
files must match the recorded bytes; a checkout that converts line endings is
not equivalent to the extracted archive. The controls run trusted variants
only and do not isolate agent-generated code. A valid counted trial still
requires the qualified runner, grading boundary and predeclared protocol.
