# External skill benchmark investigation, 2 October 2026

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

The current BenchFlow stable release is `0.7.8`, pinned at
`6614f922ad49322386b9d6083a827a3d58126710`. SkillsBench v1.1 explicitly requires
the 0.6.x runner line in its README, project dependency and registry. A newer
runner therefore requires compatibility qualification and a new protocol;
silently mixing it with historical leaderboard results would be invalid.
The current runner also pins LiteLLM 1.91.0, rather than its current stable
version. Resolve dependency/security compatibility before execution. No
upstream benchmark runner, task or oracle has been executed in this review.

## SWE-Skills-Bench: useful methodology, unavailable code endpoint

The [primary paper](https://arxiv.org/abs/2603.15401) pairs software requirements
and pinned repositories with execution tests. It reports limited benefit for
most of its 49 evaluated skills and substantial overhead in some conditions.
These are the authors' results for their tested stack, not results for this
collection or GPT-6.1 Sol. The linked GitHub repository currently returns 404;
retain that acquisition failure. The author's public ungated Hugging Face dataset is pinned at
`a111a9d9e53722c7aafd951830b459b08439f2da`, with declared MIT terms and
49 dataset rows. Rows, evaluated skills and the paper's roughly 565 task
instances are different denominators. Full data/verifier/environment review
remains pending; this acquisition does not repair the unavailable code endpoint. Publication alone does not establish adoption.

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
`>=0.6.3,<0.7`; current 0.7.8 is outside it. These are identity checks, not
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

Remaining qualification: component rights, current-runner compatibility,
trusted oracle/verifier isolation, controls and actual paired trials. Do not
pool a corrected protocol with historical leaderboard results.
