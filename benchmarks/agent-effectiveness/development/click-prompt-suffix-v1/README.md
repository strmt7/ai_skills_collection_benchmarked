# Click prompt suffix development task

This is an exposed development candidate based on a real Click issue. The
[task brief](TASK.md) and [source record](source.json) identify the pinned
revision, license, source tree and upstream fix. The 16 independent behavioral
controls check both prompt APIs, empty and nonempty suffixes, Unicode,
defaults and retries. They use a simulated command runner and do not establish
readline behavior in an interactive terminal.

The calibration runs the original source, the exact upstream patch, a
separately expressed alternative and three deliberately incomplete changes.
It verifies every extracted source file against the 142 Git blobs recorded in
`tree.json`, checks the fixed module's SHA-256, and retains each process's raw
output and case outcomes. Its manifest records file modes, but calibration
checks file contents and paths, not filesystem mode bits. The patch is a
GitHub API source-file patch with standard diff headers added and stored in a
UTF-8 JSON transport; the decoded bytes and resulting source are checked against
the recorded digests. This is not a model benchmark.

The [initial calibration records](../../../../artifacts/research/2026-11-03/click-prompt-task-calibration/)
bind the same source snapshot and control inputs on Windows and Linux. The
original fails 12 cases, the upstream patch and alternative pass all 16, and
each incomplete variant fails its expected cases. Raw local logs remain in the
research workspace; the hosted workflow retains its own raw outputs. These
controls do not establish task difficulty or compare coding agents.

## Interactive terminal controls

The separate [terminal calibration](../../../../artifacts/research/2026-11-03/click-terminal-calibration-v1/)
drives a POSIX pseudo-terminal with readline enabled. After typing and deleting
three characters, it checks the visible prompt and submitted answer for both
APIs. The recorded upstream patch, a version that removes its workaround, and
a version that gives the entire prompt to input all pass the original 16
simulated cases. The terminal control rejects the no-workaround version on
both tested runtimes.

The upstream patch preserved the prompt with the tested GNU readline build,
but not with the tested libedit build. The entire-input-prompt variant passed
these terminal cases on both; it is a positive control for this specific screen
behavior, not a complete or recommended fix for Click's output routing and
color handling. These observations do not establish behavior across all
terminals or a Windows console. Historical 16-case records bind the task files
as they existed at their recorded hashes, including the earlier task brief and
README.

The separate [output-routing calibration](../../../../artifacts/research/2026-11-03/click-routing-calibration-v1/)
checks that both prompt APIs honor `err` for the question text and still return
their answers. On the tested Windows and Linux runtimes, the upstream patch
passes those four cases. Both an `err`-ignoring variant and the terminal-only
entire-input-prompt variant fail the stderr cases, despite passing the original
16 simulated cases. The no-workaround variant passes routing and is rejected by
the separate terminal control. The routing cases check the question text,
not the stream used for every suffix byte. Neither control alone proves a
complete repair.

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

On a POSIX host with a terminal-capable CPython and readline, run the additional
control with the same extracted source and a new output path:

```sh
python benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/controls/calibrate_terminal.py \
  --source /path/to/extracted-click-source \
  --output /path/to/new-terminal-output
```

The tool records the backend, full terminal traces, rendered lines and source
digests. CI requires its positive and negative controls to separate; it reports
the upstream result rather than assuming it passes every backend. A terminal
control is still required inside the independently qualified grading boundary
before this task can support a counted trial.

The output-routing control also runs on Windows. With the same source and a
new output path, invoke:

```sh
python benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/controls/calibrate_routing.py \
  --source /path/to/extracted-click-source \
  --output /path/to/new-routing-output
```
