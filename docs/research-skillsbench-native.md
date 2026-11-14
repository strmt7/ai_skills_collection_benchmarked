# SkillsBench native evaluator qualification

The collection has no SkillsBench model score. The native evaluator validated
one public development package and ran its original verifier against the
authors' reference solution and an independently specified empty graph.

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
  and versions match the queried graph. On Linux amd64, all 140 locked projects
  installed offline from verified wheels. The unchanged BenchFlow 0.9.2 CLI
  validated the task schema and reported that the task lacks a canary string.

These are packaging and compatibility observations. They establish neither
task success nor skill utility. See the [structured evidence](../artifacts/research/2026-11-10/skillsbench-native-preflight/review.json)
and the [official distribution](https://pypi.org/project/benchflow/0.9.2/).

## Compatibility findings

The native version command passes on Windows. Package validation first failed
while reading Unicode source with the default Windows encoding. Isolated
Python ignores `PYTHONUTF8`; explicit `-I -X utf8 -B` flags cleared that error.
The unchanged evaluator then failed on an unconditional import of POSIX-only
`fcntl`. The Linux runtime provided that module and passed schema validation.

Use an explicitly qualified POSIX benchmark environment for this evaluator.
Do not stub `fcntl`, patch the installed evaluator or change the workstation's
operating system to manufacture a Windows pass. Keep benchmark environments
separate from the collection's declared Windows development toolchain.

## Native scoring contract

The selected task's original `verifier/test.sh` writes a fractional reward from
the CTRF report and exits zero even when the submission fails tests. An adapter
must retain and validate the native reward, denominator and test outcomes.
Shell exit status alone cannot establish a task pass.

The original task Dockerfile built on its pinned Linux amd64 Python 3.12.8
base. In the grading replay, each producer closed before a separate verifier
container opened. Only the two declared output files crossed that boundary.
The verifier received the task input and its own pinned files and dependencies.
It received no oracle files or producer workspace state. The two outputs
matched the collected bytes before and after grading.

| Control | Pytest cases passed | CTRF entries passed | Official reward |
| --- | ---: | ---: | ---: |
| Authors' reference solution | 35/35 | 6/6 | 1.0 |
| Empty graph | 6/35 | 0/6 | 0.0 |

The pinned CTRF plugin groups parameterized cases by test function and keeps
each group's last outcome. Keep its grouped reward and the full pytest case
counts. The verifier checks the graph outputs and does not call the requested
`parse_script` function. These limits apply to any interpretation of this
task's reward. The exposed task and oracle are excluded from untouched
confirmatory evaluation. See the [qualification evidence](../artifacts/research/2026-11-11/benchmark-qualification/review.json)
and the [execution plan](benchmark-execution-plan.md).

## Verify captured reports

The report checker supports the pinned pytest verbose output and
`pytest-json-ctrf` 0.3.6 profile. Supply the exact pytest version and the
SHA-256 of the ordered node IDs joined with line feeds, without a trailing
line feed. Freeze that inventory using a trusted verifier run before grading
submissions. The [fresh grading evidence](../artifacts/research/2026-11-11/skillsbench-fresh-grading/review.json)
records the digest and verifier source for this development control.

```sh
python tools/verify_skillsbench_pytest_reports.py \
  --ctrf ctrf.json --pytest-output pytest_output.txt --reward reward.txt \
  --pytest-version 8.3.4 --expected-node-ids-sha256 "$case_inventory_sha256"
```

The checker emits the official grouped reward, the individual pytest counts
and the raw report hashes. Missing, unsupported, or contradictory reports
return `unscored` and exit code 2. The three files must come from the same
attempt. Keep the task, submission, and environment receipts with them to
establish that association.
