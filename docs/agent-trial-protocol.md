# Coding-agent experiments

The existing 673-entry catalog readiness results describe packaging. The new
`benchmarks/agent-effectiveness/` experiments run an agent on code and score
its submitted behavior outside the task workspace. No measured skill advantage
has been established yet.

## Frozen inputs

`development/protocol-v2.json` records the task commit, source hashes, grader
hash, harness hashes, conditions, prompt template and limits before the first
counted matched attempt. The first task fixes the actual artifact validator at
commit `4bd209752567f5c35074d4ee4a73600e1c45c283`. Its external grader checks
17 acceptance cases and passes/rejects known-good and trivial bad controls.

Conditions use GPT-6.1 Sol with high reasoning effort:

- **Default:** no additional skill instructions.
- **Karpathy:** pinned third-party `karpathy-guidelines` instructions, with
  their source URL and content hash recorded. The skill declares MIT licensing.
- **Improved:** the experimental `eval-harness` and `strategic-compact` bundle.

Each recorded attempt started a fresh ephemeral CLI session with user configuration,
memory, host-skill discovery, plugins, apps and delegation disabled. The task
used the workspace-write sandbox and disabled network access. The Windows
sandbox backend is explicitly configured; execution policies are retained.

All conditions receive identical source code and pre-created empty test/log
files. The latter avoids a reproduced Windows ACL collection failure. A separate
capability check verified both agent writing and host reading, without relaxing
permissions. The planned three repetitions rotate condition order. Runs are
serial; the owner may still be doing unrelated host work.

## Evidence and failure accounting

The frozen runner recorded the launch, full CLI transcript, returned
usage, stderr, source patch, submitted tests/log, external grader result and
artifact hashes. It refused existing attempt directories and rejected changed
frozen inputs. An unsuccessful launch, timeout, missing completed turn, changed
protected source or evidence collection problem cannot become a counted pass.
Submitted code was graded in a separate process with a finite time limit.

The first independent-agent development probe passed 17/17. A CLI launch failed
because commands were unavailable; a subsequent frozen CLI attempt passed
17/17 behavior cases but could not export a sandbox-created log. Both failures
remain recorded, with their actual usage where available. They are harness
errors, not evidence of inferior model coding ability. The exact first harness
is archived with its frozen hash for audit.

## Interpretation limits

This is one development task on a real repository subset. It has already reached
the default agent's ceiling. It cannot prove superiority, broad category
coverage, or utility across the collection. The improved condition tests an
injected bundle rather than natural skill selection or individual skills.
External checks score behavior; captured agent-written tests do not establish
coverage or mutation-testing quality. Host workload is uncontrolled, so elapsed
time is diagnostic and excluded from speed claims. The CLI does not expose a
provider-resolved model snapshot; requested identity and returned usage are
reported separately.

Harder tasks, real complete repository fixtures, repeat analysis, untouched
holdouts, skill selection tests and report graphs remain required. The public
[SWE-bench Verified compatibility check](research-swe-bench-verified.md)
qualifies dataset input construction only; it is not an agent benchmark result. Do not tune
against final holdouts or omit failures to produce a favorable chart.

## Completed first matched block

All nine planned protocol-v2 attempts completed. Default, third-party Karpathy
adaptation, and the improved two-skill bundle each passed all 17 independent
checks in all three attempts. This confirms the ceiling effect; no quality gain
was demonstrated. The improved bundle's input-token range was 248,768–402,912,
versus 297,738–353,213 for default. Smaller output counts in some runs do not
establish lower total cost or consistent efficiency.

The [verified report](../artifacts/agent-trials/development-v2-report/README.md)
contains all attempts, raw token summaries and standalone charts. Its publisher
checks protocol identity, each captured evidence hash, grading consistency,
failure denominators and missing or unplanned runs. It also compares completion,
usage and completed-command counts against the captured CLI transcript. Scored
attempts must report every case in the adjacent grading manifest, which is bound
to the protocol and grader hashes, and failed or invalid-scope outcomes must
agree with their recorded evidence. The 17-case v2 manifest was reconstructed
after the trials from a Git blob matching the frozen grader hash; it was not
precommitted before those trials. It prevents consistent omission of a recorded
case during report generation, but does not prove that the grader ran or that
the observations are authentic. The quality chart separates passed, failed and
unscored attempts. With the optional reports dependencies installed, verify the
published SVG content and PNG pixels against freshly rendered charts from the
repository root:

```bash
python tools/summarize_agent_trials.py --protocol benchmarks/agent-effectiveness/development/protocol-v2.json --trials artifacts/agent-trials/development-v2 --output-dir artifacts/agent-trials/development-v2-report --check --check-plots
```

The single-task reporter derives the partition and number of matched attempts
from each protocol. Condition definitions belong to that protocol; the reporter
does not assume that another experiment used this historical three-condition
bundle. This keeps future development and holdout reports distinct without
changing the recorded historical attempts or their scores.

Future experiments must establish their case manifest before execution and
retain independent grading evidence.
For protocol version 3 or later, `grading_cases_sha256` commits the case set:
sort the unique names, serialize them as compact ASCII JSON, and hash the UTF-8
bytes with SHA-256. The adjacent `<protocol-stem>.grading.json` records that
case list, the completed protocol hash and the grader hash. The protocol also
pins `trial_manifest_sha256`, the hash of `tools/_trial_manifest.py`. Commit the
protocol and manifest before collecting attempts. The runner checks these
bindings before launching, but a hash alone does not prove when a commitment
was made or whether grading evidence is authentic.
Null usage remains null. Malformed event streams cannot produce a scored result;
their retained transcript and matching parser error are counted as a harness
failure without inventing usage or command counts. New protocols must also pin
the shared transcript parser by its `transcript_parser_sha256` before launch.
The frozen results are unchanged. Grader-created bytecode bytes are preserved
in nonexecuted `bytecode-evidence.zip` transports because loose Python caches
are correctly ignored by Git. Raw trial text is exempt from Git newline
conversion so a checkout preserves the original evidence digests.

Those trials used the original experimental `strategic-compact` overlay at its
frozen path. The later `strategic-compact-current` overlay is a separate,
unbenchmarked revision; the historical results do not measure it. See the
[token-accounting review](research-context-token-accounting.md).

The historical v2 grading driver executed submitted Python on the host in a
separate process. A newer Windows AppContainer grader has been qualified with
known-good and boundary-attack controls, but the trial runner does not yet pass
its required fixture and sandbox inputs to that grader. The frozen v2 protocol
rejects the changed execution tooling before launch. Do not run a new model
trial until the runner and confined grader are integrated and independently
qualified. The runner now refuses new model launches before creating a workspace
or starting a process until those prerequisites are implemented. It also rejects
scored grader responses whose cases, counts or outcomes disagree with the frozen
case set. The historical evidence establishes neither container isolation nor
provider-resolved model identity.

The Windows job-process control limits output and cleans up job members. It is
not a complete sandbox: Microsoft documents that processes created through
`Win32_Process.Create` are not automatically assigned to the caller's job.
Before integrating it into trials, qualify the agent sandbox's service access
and the full collection and grading boundary. See [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## Comparing multiple task reports

`tools/summarize_multi_task_trials.py` reads a declared plan of task IDs,
protocol hashes, protocol paths and trial directories. It revalidates every
single-task report, rejects missing attempts, duplicate tasks, changed protocol
bytes and mismatched model, partition or condition definitions, then preserves
per-task attempts and their result hashes, status counts, matched-block
comparisons, grading provenance, limitations and model-snapshot availability. It reports pass-rate differences
with equal weight per task using exact fractions. If either compared condition
has an unscored attempt on any planned task, its aggregate difference is
unavailable; that attempt remains visible rather than being counted as a fail
or silently dropped.

The `paired_outcomes` section also separates blocks where both conditions
passed, only the candidate passed, only the default passed, neither passed, or
at least one attempt was unscored. It reports both pooled block counts and the
average of each task's outcome fractions, giving every task equal weight even
when repetition counts differ. Fully scored tasks are counted as candidate
ahead, default ahead or equal according to their observed pass-rate difference;
any task with an unscored block is counted separately. Equal net differences
can therefore be distinguished from agreement on individual blocks.

These are descriptive summaries, not confidence intervals or significance
tests. Pooled repetitions need not be independent, task identity alone does
not establish independence, and unscored results remain unknown. Research on
[paired evaluation](https://aclanthology.org/2021.acl-long.179/) motivates
retaining paired outcomes; it does not validate a superiority claim for this
experiment.

For each comparison, `missing_outcome_sensitivity` reports exact lower and
upper bounds from hypothetical pass/fail assignments for all unscored attempts.
For each task, the lower bound assigns unscored baseline attempts passes and
unscored candidate attempts failures; the upper bound assigns the opposite.
The planned attempt count remains the denominator, and the task bounds are
averaged with equal task weight. The report retains per-task bounds and missing
counts. When every attempt is scored, both bounds equal the observed mean.
These assignments do not turn an unscored attempt into an observed outcome:
for an invalid-scope attempt there may be no meaningful binary outcome without
correcting the experiment. The range is not a confidence interval, a rerun
prediction or a superiority test and does not cover other sources of bias.

For each comparison, `model_snapshot_evidence` counts matched pairs with equal,
different or incomplete provider-reported snapshot identifiers. It also lists
the identifiers observed across all planned tasks. The status is
`inconsistent_reported_identifiers` when more than one identifier appears,
even if the identifiers happen to match within every pair; otherwise it is
`incomplete` when any pair lacks an identifier, or
`single_reported_identifier` when all pairs report the same one. Different
identifiers may reflect aliases or changed models; matching identifiers are
not independent proof that the underlying model was unchanged. The descriptive
outcomes remain visible, but inconsistent or missing metadata limits causal
interpretation of the comparison.

The report also summarizes matched input and output token differences. A block
is comparable only when both attempts passed and both recorded usage. It first
averages the paired deltas within each task, then weights tasks equally. A
task mean is unavailable if any of its planned blocks is not comparable; the
across-task mean is unavailable if any task mean is missing. Counts and
individual blocks remain visible. Input includes cached input and output
already includes reported reasoning output. These counts are not priced cost,
statistical significance or proof of greater efficiency.

The separate `all_attempt_usage` section accounts for reported input and output
tokens across every attempt status, including failed and unscored runs. It shows
observed subtotals and usage availability by status and task. Per-task means,
equal-task means and condition-minus-default differences are available only
when all required usage records are present; missing usage is never treated as
zero. This view describes all recorded attempts, so its differences may combine
different outcome mixes. It is not a success-matched comparison, a priced-cost
calculation, or proof of efficiency. Cached input is already included in input;
reported reasoning output is already included in output.

Run the read-only tool with `--plan <plan.json>`. The
[historical example plan](../benchmarks/agent-effectiveness/development/multi-task-historical-example.json)
reads the already recorded v2 trials. It was created after those trials and is
not preregistration or a new experiment. It contains one task and therefore
reports the existing zero difference without establishing an advantage. A plan
hash alone cannot prove when a plan was committed, whether tasks are independent,
or whether a grader actually ran. These descriptive figures are not a
significance test, collection-wide conclusion, priced-cost comparison or evidence
of a provider-resolved model identity.

For Python 3.11–3.14, install the `reports` extra from the repository root with
`python -m pip install '.[reports]'`. The maintainer's
`requirements-reports-lock.txt` is generated for the hosted Python 3.14 report
job; it is not a lock for every supported Python version. The compatibility
matrix uses uv-managed CPython builds for Windows 3.11 and 3.12, because the
GitHub-hosted Python catalog does not provide those current patch releases for
Windows; the other matrix jobs use GitHub's Python setup action.

With the `reports` extra installed, render the same verified plan with
`python tools/render_multi_task_chart.py --plan <plan.json> --output <chart.svg>`.
Add `--check` to compare an existing chart without writing it. Dots show scored
individual tasks and the square shows the equal-task mean only when every
planned task in that comparison is scored. Unscored tasks remain counted, and
points may overlap. When outcomes are unscored, a separate line shows their
hypothetical sensitivity bounds; it is not a confidence interval. The chart
recomputes those bounds and status counts from the recorded attempts before
rendering. The offline-validation workflow tests and uploads a chart
for the historical example; it shows no demonstrated advantage. Rendering
checks require the reports dependencies and run in that workflow's report job.
The chart also counts attempts without snapshot metadata and distinct reported
snapshot identifiers. These are reported metadata, not independently verified
provider identities; distinct identifiers can make comparisons harder to interpret.
Each candidate row also shows its identifier status and the number of matched
pairs with different or incomplete identifiers. `IDs: vary` includes identifiers
that differ between tasks even when each individual pair matches.

Use `--view paired` with the same command to render the paired-outcome chart.
Its stacked bars show the equally task-weighted fractions for both passes,
candidate-only passes, default-only passes, neither passing and unscored blocks.
Task-direction counts and pooled block counts are annotations, not the bar's
denominator. Percentages are rounded; small segments are left unlabeled and
unscored segments are hatched. The renderer checks the paired summary against
the recorded attempts; displayed snapshot IDs are provider-reported and are not
independently verified. The workflow also uploads this view for the historical
plan; it is descriptive and does not establish significance or superiority.

For paired token differences, use
`python tools/render_token_chart.py --plan <plan.json> --output <chart.svg>`.
The two panels show input and output counts separately, with complete task means,
the equal-task mean when all tasks are complete, comparable block counts, and
the same per-candidate snapshot evidence.
The workflow also uploads this chart. It describes observed usage; it does not
establish priced cost, efficiency, statistical significance or agent superiority.
