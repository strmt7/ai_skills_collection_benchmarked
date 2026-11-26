# External skill benchmark investigation

The repository already registers SkillsBench and SWE-Skills-Bench. Their existing
adapters test repository resolution and metric descriptions. They do not execute
tasks or establish skill efficacy. Keep these evidence classes separate.

## SkillsBench: primary integration candidate

[SkillsBench 1.1](https://www.skillsbench.ai/blogs/skillsbench-1-1) publishes 87
native task packages across eight domains. Its paired conditions use the same
task and environment with and without curated skills; verifiers and withheld
oracles establish task outcomes. Invocation tracking distinguishes available
skills from skills actually read. The task roster, historical paper inventory
and live leaderboard configuration counts are different versioned objects.

There is evidence of industry adoption: [GitHub's June 2026 evaluation](https://github.blog/ai-and-ml/github-copilot/evaluating-performance-and-efficiency-of-the-github-copilot-agentic-harness-across-models-and-tasks/)
includes SkillsBench alongside broader engineering and terminal suites.
That is stronger evidence than the benchmark's own popularity claims; it does
not establish a universal certification standard for individual skills.

The highest published stable SkillsBench release is `v1.1`, resolved through
all GitHub release pages to `b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af`.
Its root license is Apache-2.0, but bundled skills carry additional component
licenses. Review individual selected task/resource rights before redistributing.
Exact source acquisition is recorded in `skill-benchmark-source-review.json`.

The BenchFlow release reviewed on 2 October was `0.7.8`, pinned at
`6614f922ad49322386b9d6083a827a3d58126710`. On 30 October,
[PyPI's package API](https://pypi.org/pypi/benchflow/json) reported `0.7.11`
as the latest non-yanked stable release. SkillsBench v1.1 explicitly requires
the 0.6.x runner line in its README, project dependency and registry; both
0.7.8 and 0.7.11 fall outside that range. A newer runner therefore requires
compatibility qualification and a new protocol; silently mixing it with
historical leaderboard results would be invalid. The previously reviewed 0.7.8
runner pins LiteLLM 1.91.0. Resolve dependency/security compatibility before
execution. No upstream benchmark runner, task or oracle has been executed in
this review.

The 30 October native PyPI response has SHA-256
`9d5221750701569b0f25bad7071e33bcbfaf5887bc1ab9de489905f14f9a2e7b`;
the source-locked SkillsBench registry has SHA-256
`ade4beaad3092cdbe9870f54e6a3e222e71f53be3527ec539ae002e1d6e5f3be`. These
checks identify published versions and constraints; they do not test runner
compatibility or benchmark performance. The [recorded comparison](../artifacts/research/2026-10-30/skillsbench-currentness/result.json)
includes the source identities and range-membership results.

## SWE-Skills-Bench and its public results

The [primary paper](https://arxiv.org/abs/2603.15401) pairs software requirements
and pinned repositories with execution tests. The first review records a 404
for the paper's repository link. A subsequent review retrieved the publisher's
[code and results](https://github.com/ControllableModel/SWE-Skills-Bench/tree/4d3450d9216a590a8726fcb3604b5143daca776b)
and reproduced four comparisons of 980 matched requirements each. Across those
configurations the mean changes ranged from −0.29 to +0.76 percentage points.
See [archive verification and native controls](research-swe-skills-bench-archive.md).

The authors' earlier Hugging Face dataset at
`a111a9d9e53722c7aafd951830b459b08439f2da` contains 49 rows under declared MIT
terms. The 49 rows, the original paper's task counts, and the later archive's
matched comparisons refer to different populations. Results for this
collection and GPT-6.1 Sol require a new matched experiment.

## TestEval for Python test generation

TestEval measures whether generated Python tests execute and what code they
cover. On three public development tasks, the native evaluator reported
identical execution and coverage for matching and deliberately failing
assertions. It also reported zero execution and coverage for three tests
that passed under pytest with a different name and invocation form. Publish
the native metrics alongside independent checks of assertion outcomes.
[Benchmark paper](https://arxiv.org/abs/2406.04531) · [15 paired controls](../artifacts/research/2026-11-25/testeval-public-controls/result.json)

Across all 12 public pilot tasks, the publisher gave the same metrics to
exact, shape-only and incorrect assertions using the same calls. The exact
suites passed on the reference and detected all 24 controlled result faults.
The shape-only suites passed on the reference and detected zero. The
independent runner rejected all 12 incorrect suites on the reference. These
controls qualify the measurement method with authored tests.
[Public pilot grader review](../artifacts/research/2026-11-25/testeval-pilot-grading/review.json)

### Grade a native final message

For a first-turn study, freeze the original publisher task, installed runner
and grader, prompt digest, comparison arms, and scoring rules before inference.
Keep the workspace-submission and final-message studies separate. The first-turn
study sends one test string to the publisher's overall evaluator. Its scope
covers that single response.

Use an admitted owned native runner. Save its exact request as `input.native`,
native process receipt as `process.json`, and JSON events as `transcript.jsonl`.
Use the native client's `--output-last-message` option to save
`last-message.native` in controller-owned state outside the subject workspace.
The collector checks the completed turn, process cleanup, frozen prompt digest,
and byte agreement between the last-message export and final transcript item.
It then seals a controller envelope for the existing publisher and independent
reference and defect graders.

```text
python tools/collect_testeval_reply.py --plan <task-plan> --baseline <baseline> --execution <native-records> --prompt-sha256 <frozen-digest> --defects <fixture-dir> --assets <assets-dir> --runtime <runtime-plan> --output .venv/reports/testeval-reply
```

Use the paths and digest from the frozen study. The execution records and new
output directory belong under the controller's `.venv`. Retain the delivery
receipt, original grader result, and independent reference and defect results.
[Publisher evaluation instructions](https://github.com/LLM4SoftwareTesting/TestEval/blob/6f67dee71de6ccda1767b8c219a93f4ae0a7ce90/README.md#run-your-own-pipeline)


### Inspect a completed turn before grading

A completed native turn can consume its output budget without delivering a final
message. Inspect the native process and transcript using the frozen request digest.

```text
python tools/inspect_testeval_reply.py --execution <native-records> --prompt-sha256 <frozen-digest> --turn-output-budget 32
```

Use the budget declared for the whole turn. Omit the option if the study has no
turn-level token budget. The inspector checks the request, process closure and
transcript. When a final reply exists it checks the exact CLI export. It reports
delivery separately from usage below, at or above the declared budget, or reports
unavailable usage. A successfully inspected missing reply is an ungraded outcome.
When a turn makes several requests, the CLI's total usage covers the turn. Validate
any per-request limit with independent backend evidence.

On the qualified local Ollama setup, 16- and 32-token model limits stopped native
chat at the configured counts. The Responses streams reported completion at those
counts. A single Codex CLI request reached 32 output tokens with an empty final
export. These controls establish delivery and budget behavior for the recorded
configuration. [Native output budget evidence](../artifacts/research/2026-11-26/native-output-budget/observations.json)

For a private Ollama trial, use the pinned publisher manifest and its verified
blob cache to build a separate model store before starting the local server.

```text
python tools/stage_ollama_model.py --model qwen3:4b --manifest <pinned-manifest> --manifest-sha256 <digest> --cached-blobs <blobs-directory> --output .venv/benchmarks/local-model
```

The output parent must exist. The stage verifies every blob and writes the
manifest after the copies pass. Ollama updates blob timestamps when deriving
models, so use the staged store for that operation. The live isolation control
reproduced both derived model identities while preserving the shared weight's
file identity, byte count and modification time.

## Do not rely on benchmark reputation alone

[OpenAI's February review](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
identified contamination and flawed tests in SWE-bench Verified. Its
[July review](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
then estimated that roughly 30% of SWE-bench Pro tasks were broken and withdrew
its earlier recommendation. A newer or widely reported suite still needs
prompt/test agreement, meaningful coverage, known-good controls and resistance
to reward hacking. Record disputed tasks; do not remove inconvenient failures
after seeing model results.

Integration must preserve pinned tasks and independent outcomes, keep oracles
and verifiers outside solver access, review actual container isolation, and
record every attempt. Freeze category/task sampling before evaluation. Compare
default, original Karpathy-attributed instructions, upstream curated skills and
this collection's revised skills with the same requested GPT-6.1 Sol high
configuration. Distinguish unavailable resolved model identity, actual skill
invocation, input/output/cache usage, infrastructure failures and task failures.
Use task-level paired uncertainty across repetitions; do not publish only the
best run. Include new owner-inspired cases and untouched holdouts so public
benchmark performance is not the sole quality claim.

The published v1.1 registry pins task commit
`55bfe693f2a19f6b2f29aca3f54fe98b9d994668`. All 87 task content digests were
independently recomputed and matched. The registry's exact runner range is
`>=0.6.3,<0.7`; both inspected 0.7.x versions are outside it. These are identity checks, not
correctness, security or license clearance. Most tasks request public networking.

Before reading engineering task prompts, skills or verifiers, the 23 primary
software-engineering/cybersecurity tasks were split deterministically into
12 development and 11 holdout tasks, stratified by category. The seed, algorithm,
task IDs and hashes are recorded in `skillsbench-engineering-partitions.json`.
Holdout semantics remain unread; public metadata exposure does not establish
that the model itself has never encountered the public benchmark.

The development parallel-TF-IDF verifier has an independently reviewed empty-
output acceptance defect: it zips result lists without checking their lengths.
Its speed checks use one ordered observation, and candidate imports share the
verifier process. Preserve the upstream test and report corrected grading under
a new protocol with known-bad controls and external expectations/clocks.
See `research-parallel-search-benchmark.md`. No task or model run is scored yet.

A second development task, `python-scala-translation`, has a Dockerfile that
copies a near-identical Scala implementation into the image, and its verifier
can report a pass after a simulated nonzero test exit. The [source-bound review](research-skillsbench-scala.md)
records the controls and their limits. No Scala task or model run was scored.

For the development task `dialogue-parser`, the upstream test module accepted
a derived output-only fixture without the required parser and with an unrelated
DOT edge. The [controlled review](research-skillsbench-dialogue.md) also
records the original fixture failure and a negative visualization control. It
does not report a benchmark-harness or model score.

For `fix-visual-stability`, a [real-browser control](research-skillsbench-visual.md)
shows that the theme-flicker predicate accepts an inert script containing its
keywords. This tests one predicate, not the complete task or a model run.

Remaining qualification: component rights, current-runner compatibility,
trusted oracle/verifier isolation, controls and actual paired trials. Do not
pool a corrected protocol with historical leaderboard results.

For `flink-query`, a [controlled comparison](research-skillsbench-flink.md)
shows that duplicate output rows are not detected by the upstream set-based
check. It does not run Flink or score a model.

For `simpo-code-reproduction`, a [controlled verifier review](research-skillsbench-simpo.md)
shows that regenerated output is not reloaded before its numerical comparison.
It does not run the training task or score a model.
