# SkillsBench Flink development-task review

This review concerns the public development task
[`flink-query`](https://github.com/benchflow-ai/skillsbench/tree/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query)
at the task commit pinned by SkillsBench v1.1. The task asks for one output
tuple per job. Its [output check](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query/verifier/test_outputs.py)
converts both expected and actual lines to sets, so it does not compare
multiplicity.

The pinned [expected output](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query/verifier/out_lsj_001a.txt)
contains 644 records for 644 distinct job IDs. A controlled call to the
original comparison accepted both those 644 lines and a 645-line output with
one identical duplicate. It rejected an output missing a line and another
with a new extra line. Consumers requiring one record per job cannot rely on
this check to detect duplicates.

The [control](../artifacts/research/2026-10-30/skillsbench-flink-comparison/reproduce.py)
checks the exact verifier and expected-output hashes, routes the fixed output
path to isolated temporary files, and runs those four cases. The
[Windows](../artifacts/research/2026-10-30/skillsbench-flink-comparison/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/skillsbench-flink-comparison/linux-result.json)
results agree; an altered expected input was rejected by the hash check.
Run `--help` for the two required pinned source files.

This exercises only the output-comparison function. It does not compile or run
Flink, execute the benchmark harness, validate every query semantic or score a
model. No held-out task content was read. Preserve the upstream test and report
any multiplicity-aware replacement under a distinct predeclared protocol.

## A separate multiplicity-aware comparison

`tools/compare_flink_outputs.py` compares an independently supplied, nonempty
reference with a candidate file. It parses each `(jobId,count)` tuple, rejects
duplicate job IDs in either file, and compares counts without depending on row
order. For example:

```bash
python tools/compare_flink_outputs.py --expected reference.txt --actual out.txt --json
```

The process exits zero only when the parsed records agree. It reports missing,
extra and mismatched IDs; malformed lines and duplicate IDs fail. The reference
must be obtained and validated independently: the comparator cannot establish
that its contents are correct, that a Flink job ran, or that an agent solved a
task. Its rules are a distinct development protocol, not the upstream verifier;
predeclare its use in any future experiment and do not replace prior scores.
The [source-bound control](../artifacts/research/2026-10-30/flink-comparator-control/reproduce.py)
exercises the pinned 644-row reference and matching, reordered, duplicate,
missing and extra cases. The [Windows](../artifacts/research/2026-10-30/flink-comparator-control/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/flink-comparator-control/linux-result.json)
results agree. These controls do not constitute a model benchmark.
