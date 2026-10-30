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

## Independent reference reconstruction

A separate Python reference algorithm reads the pinned development task's
[job events](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query/environment/workspace/data/job_events/part-00001-of-00500.csv.gz)
and [task events](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query/environment/workspace/data/task_events/part-00001-of-00500.csv.gz).
It identifies FINISH job events and SUBMIT task events using the column and
event definitions in the supplied
[trace schema](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/flink-query/environment/workspace/data/format.pdf),
sorts submission times per job, and counts the largest session. Repeated
submissions are counted separately. The trace documentation credits John
Wilkes and Charles Reiss and states that the data and documentation are
available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

For jobs with both an observed FINISH and an observed SUBMIT, the algorithm
reconstructed all 644 supplied reference records exactly. It tested both
splitting at an exact ten-minute gap and splitting only after that gap; no
observed adjacent submissions were exactly ten minutes apart, so this dataset
cannot decide the boundary convention. No observed submission for those jobs
occurred after their last observed FINISH.

The supplied files also contain 54 finished job IDs without an observed task
submission and 590 submitted job IDs without an observed FINISH. Neither group
appears in the supplied reference. Whether a task should emit zero for the
former, or handle the latter differently, needs an explicit task contract and
additional data; the reconstruction does not resolve those cases.

The [source-bound control](../tools/reconstruct_skillsbench_flink.py)
accepts the two pinned compressed inputs and pinned reference as arguments.
Its [Windows](../artifacts/research/2026-10-30/flink-reference-reconstruction/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/flink-reference-reconstruction/linux-result.json)
results agree. Synthetic tests cover session boundaries and repeated submits;
an altered input fails its digest check. This is a reference-data control, not a
Flink execution or an agent benchmark. The independent comparator above still
requires a separately predeclared protocol before it is used for scoring.
