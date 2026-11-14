# SWE-Skills-Bench archive verification

SWE-Skills-Bench tests whether a supplied skill helps an agent complete
requirements in a repository. We reproduced the authors' published aggregates
for 980 paired requirements per configuration. Each pair compares the test
pass rate with one publisher skill against the pass rate without that skill.
See the [paper](https://arxiv.org/abs/2603.15401v2) and the
[pinned result tables](https://github.com/ControllableModel/SWE-Skills-Bench/tree/4d3450d9216a590a8726fcb3604b5143daca776b/results/final_results).

| Publisher configuration | No skill | One skill | Mean change |
| --- | ---: | ---: | ---: |
| Claude Code / Haiku 4.5 | 74.2% | 74.5% | +0.26 pp |
| Claude Code / Kimi K2.6 | 78.5% | 79.2% | +0.64 pp |
| Codex / GPT-5.4 mini | 76.0% | 76.7% | +0.76 pp |
| Codex / Kimi K2.6 | 77.6% | 77.3% | −0.29 pp |

The mean change uses the publisher's paired delta column. The arm means are
shown at the publisher's display precision. All 3,920 pairs matched between
the separate and combined result tables. Omitting one declared repository
group at a time produced the ranges recorded in the
[verification evidence](../artifacts/research/2026-11-11/swe-skills-bench-archive/review.json).
These ranges describe how the reported means vary with group membership.

## Reproduce the archive check

Save the four per-configuration `*_cells.csv` files from the pinned result
directory without changing their bytes. From this repository, run:

```text
python tools/verify_swe_skills_bench_results.py --frame artifacts/research/2026-11-11/swe-skills-bench-archive/frame.json --tables-dir <publisher-csv-directory>
```

The checker validates the file digests and every expected skill and batch
pair before producing aggregates. A mismatched or incomplete archive fails.

## Public development control

We selected `batch1/python-anti-patterns` using package metadata before
reading the task or verifier. All 110 files in the Boltons source snapshot
matched the pinned Git tree. Each control ran the original verifier in a fresh,
network-disabled container from the publisher's digest-pinned Linux image.
The verifier ran as an unprivileged user. JUnit counts, the console summary
and the exit status agreed.

| Input | Benchmark checks passed |
| --- | ---: |
| Unchanged pinned Boltons source | 10 / 10 |
| Same source with a syntax error in one target module | 7 / 10 |

The unchanged revision also passed all 431 tests in its upstream suite. Its
10/10 starting score leaves zero headroom on this cell. Keep the cell for
development controls and exclude it from untouched evaluation because its
task and verifier were inspected. The run used a local Docker lease and the
publisher's pytest command with JUnit capture. Published-run equivalence
would require matching the historical enroot image and agent harness.
See the [development evidence](../artifacts/research/2026-11-11/swe-skills-bench-native/review.json).

## Accepting a native score

The pinned publisher evaluator correctly mapped both Boltons runs. It also
assigned 1.0 when a synthetic transport returned the console prefix through
the first passing test and then exited with code 2. The result gate now
requires the full frozen test inventory, a terminal console summary, matching
JUnit case outcomes and a consistent exit code before accepting a fraction.
The truncated run, missing pytest, empty collection and timeout all yielded
an unverified result with no score. See the
[evaluator replay](../artifacts/research/2026-11-11/swe-skills-bench-score-admission/review.json).

Use `tools/verify_swe_skills_bench_pytest_result.py` with the controller's
`--console`, `--junit`, `--publisher-result` and `--exit-code` evidence,
plus an independently frozen `--inventory`. The
[Boltons inventory](../artifacts/research/2026-11-11/swe-skills-bench-score-admission/pytest-inventory.json)
is a development example. This profile admits completed pass/fail cases.
The [Packaging profile](../artifacts/research/2026-11-11/swe-skills-bench-candidate-skips/pytest-inventory.json)
also declares one candidate-caused skip. Use its `--submission-manifest` and
`--handoff-result` to bind the native verdict to the completed reconstruction.
The exact skip reason must match, and the required demo file must be absent
from the complete capture. The skipped check stays in the denominator and
earns no passing count. Unknown skips and collection errors remain unverified.
Keep those attempts in the run accounting and resolve their cause before
reporting comparisons.

A second exposed cell used the pinned PyPA Packaging source. A scripted
producer emitted two files, and the controller verified their bytes and
closed the producer before opening a fresh grader. The complete fixture
passed 11/11 checks. The same tests with a runnable but incomplete demo passed
10/11. The grader imported Packaging from the pinned source, and the
publisher and gate agreed on both fractions. See the
[transfer evidence](../artifacts/research/2026-11-11/swe-skills-bench-score-admission/packaging-transfer.json).

## Transfer a collected submission

`tools/transfer_benchmark_submission.py` seals changes between two completed,
controller-owned workspace captures. It supports file additions, edits,
deletions, empty files and directory layout. An unchanged submission produces
a valid zero-change archive. An incomplete collection fails before an archive
is accepted.

```text
python tools/transfer_benchmark_submission.py --baseline-manifest baseline.json --submission-manifest submitted.json seal --submission-tree collected-source --bundle delta.tar
python tools/transfer_benchmark_submission.py --baseline-manifest baseline.json --submission-manifest submitted.json restore --baseline-tree pinned-source --bundle delta.tar --archive-sha256 <controller-digest> --output fresh-grader-source
```

Use receipts from the repository's bounded collector after subject execution
has stopped. Supply the baseline and submission receipts separately from the
archive, and pass the digest returned by `seal` to `restore`. Reconstruction
checks both snapshots and the changed bytes before reporting success.
Tasks that depend on executable-bit changes require an additional mode contract.

The Windows collector sealed both an unchanged Packaging capture and its
two-file edit. Fresh Linux graders reconstructed both. The edit passed
11/11 checks. The unchanged source reached ten failures and one
candidate-caused skip. The declared Packaging policy admitted the publisher's
0/11 score on both Windows and Linux. Five controls with inconsistent source
evidence, a wrong skip reason or incomplete output withheld a score. See the
[skip qualification](../artifacts/research/2026-11-11/swe-skills-bench-candidate-skips/review.json).
An altered archive
was rejected before a grader workspace was created. See the
[handoff qualification](../artifacts/research/2026-11-11/swe-skills-bench-handoff/review.json).

The [native controller](native-benchmark-controller.md) connects completed
collection receipts, source handoff, fresh grader execution, publisher scoring
and result admission in one command. It reproduced both Packaging scores and
rejected failed or interrupted collections before opening containers.

## Use in a new benchmark

The frame contains 90 declared repository groups and one skill whose source
comes from an image without a declared repository revision. The configuration
lists 12 image references without digests. The published runs used enroot.
Qualify and pin the source, image and execution backend for a new trial.
Independently freeze task selection, skills and the analysis plan before model
runs, and account for tasks sharing a repository.

The archive contains results for the publisher's skills. None of its 98 skill
entrypoints exactly matches any of the 673 collection mirrors by bytes. The
archive replay processed result tables and metadata. Development controls
exposed two cells, which remain excluded from untouched evaluation. Local
model comparisons with the default agent and Karpathy baseline remain pending.
