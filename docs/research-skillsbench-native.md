# SkillsBench native evaluator preflight

The collection has no SkillsBench model score. The 10 November preflight
admitted one public development package and its official evaluator; native
oracle and verifier qualification remain open.

## Verified inputs

- SkillsBench revision `f860ecf02ef53412a030f8661c83d644b739ff01` contains
  87 native task packages. `dialogue-parser` was selected for development
  qualification before reading its task and oracle contents. Its 14 selected
  source and repository metadata files match their pinned Git blob identities.
- The official BenchFlow 0.9.2 wheel matches publisher SHA-256
  `0ede69cab59e8c397c58e80d3c68d60240ede0722c03e495dbd2400329d9cf9e`.
  Its complete archive contains 601 files. Installation verified 600 unchanged
  files; the installer-rewritten `RECORD` is excluded from that byte comparison.
- Windows and Linux dependency resolution produced complete hashed graphs of
  141 and 140 projects. The OSV API reported no matching advisories for those
  exact coordinates at capture time. All 141 installed Windows project names
  and versions match the queried graph. Linux runtime installation was not run.

These are packaging and compatibility observations. They establish neither
task success nor skill utility. See the [structured evidence](../artifacts/research/2026-11-10/skillsbench-native-preflight/review.json)
and the [official distribution](https://pypi.org/project/benchflow/0.9.2/).

## Compatibility findings

The native version command passes on Windows. Package validation first failed
while reading Unicode source with the default Windows encoding. Isolated
Python ignores `PYTHONUTF8`; explicit `-I -X utf8 -B` flags cleared that error.
The unchanged evaluator then failed on an unconditional import of POSIX-only
`fcntl`. Schema validation failed; structural validation was not run.

Use an explicitly qualified POSIX benchmark environment for this evaluator.
Do not stub `fcntl`, patch the installed evaluator or change the workstation's
operating system to manufacture a Windows pass. Keep benchmark environments
separate from the collection's declared Windows development toolchain.

## Native scoring contract

The selected task's original `verifier/test.sh` writes a fractional reward from
the CTRF report and exits zero even when the submission fails tests. An adapter
must retain and validate the native reward, denominator and test outcomes.
Shell exit status alone cannot establish a task pass.

Next, qualify the authors' oracle and a meaningfully incorrect submission in
the declared task environment. Preserve the original scorer, task files and
dependency boundaries. Inspect its coverage limits and retain failures before
admitting model trials. The exposed development task and oracle are excluded
from untouched confirmatory evaluation, and their answers must never enter
candidate skills. Follow the [execution plan](benchmark-execution-plan.md).
