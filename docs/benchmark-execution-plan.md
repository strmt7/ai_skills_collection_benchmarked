# Independent benchmark execution plan

The objective is a practically meaningful improvement over the same agent
without collection instructions and over the pinned Karpathy-derived baseline.
No such improvement has been established. Repository tests, source probes,
package readiness and local evaluator controls cannot establish it.

This plan follows the [11-source official-documentation review](../artifacts/research/2026-11-10/official-benchmark-planning/sources.json)
and the [earlier benchmark review](benchmark-expansion.md). The current registry
contains 18 reference methods, including frameworks as well as datasets. Three
additional execution candidates were reviewed: τ-Bench, LiveCodeBench and
ProgramBench. These counts are not counts of completed benchmark evaluations.

The [native SkillsBench preflight](research-skillsbench-native.md) admitted the
current task format and BenchFlow 0.9.2 distribution. It preserved two Windows
compatibility failures and resolved separate platform dependency graphs. Native
oracle/verifier execution and full harness qualification remain required;
installation and the version command are not benchmark results.

## Execution priorities

Use the authors' datasets, scoring implementations and native result formats.
An integration adapter transports inputs and results; it must not rewrite the
grader, expected answers or acceptance thresholds. Preserve published version
boundaries and label partial runs explicitly.

| Priority and method | Evidence sought | Native admission requirements |
| --- | --- | --- |
| 1. [SkillsBench](https://www.skillsbench.ai/docs/getting-started) | Direct effects of skills across professional tasks. | Current documentation uses BenchFlow `task.md` packages, outcome verifiers and an oracle sanity check. Pin the package, BenchFlow, agent harness and sandbox. Compare explicit skill modes on the same package. |
| 1. [SWE-Skills-Bench](https://github.com/ControllableModel/SWE-Skills-Bench) | Skill utility in repository development. | Audit task/oracle independence, skill provenance and task coverage before admitting its paired comparisons. |
| 2. [SWE-bench Verified](https://www.swebench.com/) | Real issue resolution and regression behavior. | Pin the split, repository revision, official evaluator and images. Keep the agent harness constant; a published mini-SWE-agent score is not a Codex baseline score. |
| 2. [SWE-Bench Pro V2](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2) | Longer changes across repositories and languages. | Use the V2 task definitions and native regrading environment; retain its actual split and denominator. |
| 2. [Terminal-Bench 4.1](https://github.com/harbor-framework/terminal-bench/releases/tag/v4.1.0) | Terminal workflows and reliable tool use. | Use native Harbor scoring and pinned task packages. Full and CPU-only datasets are separate populations. |
| 2. [DeepSWE](https://github.com/datacurve-ai/deep-swe) | Longer engineering tasks and clean-environment regression checks. | Qualify the selected release, environment and native verifier; repository resolution is insufficient. |
| 3. [ProgramBench](https://programbench.com/) | Complete implementations of observable program behavior. | Preserve the provided binary/documentation boundary and hidden behavioral evaluator. Full resolution is primary; its separate Almost metric cannot replace it. |
| 3. [LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) | Code generation, repair, execution and output prediction. | Freeze an explicit release and dataset revision; `release_latest` is mutable. Report these narrower capabilities separately from repository-agent results. |
| 3. [BFCL V4](https://gorilla.cs.berkeley.edu/leaderboard.html) | Function selection, arguments and multi-turn tool use. | Pin categories and the official checker. Tool-call accuracy does not establish complete software-engineering ability. |
| 3. [τ-Bench](https://github.com/sierra-research/tau2-bench) | Stateful tool use and policy adherence. | Freeze the released text frame, cell binding revisions, agent and simulated-user settings. A simulated benchmark user is part of the task, not human assistance. |
| 3. [ScienceAgentBench](https://osu-nlp-group.github.io/ScienceAgentBench/) | Scientific programming and output correctness. | Qualify data rights, dependencies and discipline-specific oracles. Successful execution alone is insufficient. |
| 4. [WebArena Verified](https://github.com/ServiceNow/webarena-verified) and [WorkArena](https://github.com/ServiceNow/WorkArena) | Browser and enterprise application-state outcomes. | Use approved disposable environments and native state evaluators. Browser frameworks alone supply no benchmark score. |

Review every other registered method for additional coverage, including ML
engineering, operating-system interaction and repository workflows. Record why
a method is admitted, deferred or unsuitable. Select for relevant capability
coverage and independent scoring, never for the largest observed skill gain.
Record gaps where established suites do not exercise a catalog skill.

## Qualification before model calls

For each admitted suite, first reproduce an authors' public development oracle
and a meaningfully incorrect submission through the native scorer. Retain raw
results and verify that both are classified correctly. These are environment
and evaluator controls, not model performance. Inspect benchmark-provided skills
for task-answer leakage before treating their comparison as independent.

Qualify the actual controller, model transport, tool surface, instruction
isolation, execution, collection and grading boundary. Keep the current model
launch refusal until this complete boundary passes. Use fresh serial subjects
under the [owner's benchmark policy](benchmark-subject-policy.md); no delegated
development agents or parallel model trials.

Keep the workstation on its declared Windows x64 target. Qualify suite-specific
hosted or container environments separately, with explicit dependencies and
cleanup. SkillsBench currently documents Modal cloud execution and optional
Docker execution. Do not assume either runtime or its credentials exists.
Provision maintained tools in owned environments. Preserve benchmark-author
environment versions for native comparisons; silently upgrading an evaluator's
dependencies changes the experiment.

## Matched experiment design

Freeze the task selection and analysis before confirmatory outcomes. Compare:

1. The same agent/model under the common benchmark constraints, without
   collection instructions, host skills or development memory.
2. The pinned Karpathy-derived baseline under identical conditions.
3. The candidate collection or declared individual skill under those conditions.

The Codex baseline measures Codex in that experimental environment. Other
authors' reference agents remain separately labelled. Record the exact model,
provider-resolved identity when available, reasoning settings, harness, ordinary
tools, task inputs, budgets, environment and invocation order. A requested model
name is not proof of a resolved snapshot. Keep unavailable metadata explicit.

Test content, natural routing, correct non-activation, individual skills and
bundles separately. Include length-matched irrelevant controls and justified
component ablations. Only the declared intervention may vary. Test transfer
across task families, repositories, agents and multiple model families; select
current supported model identities from official provider catalogs before runs.

## General improvement without answer fitting

Use development failures to identify transferable causes: incomplete contracts,
bad tool selection, premature changes, missing regression checks, unsupported
dependencies or excessive context. Research and repair those causes. Preserve
attributable original text and immutable mirrors. Evaluate new overlays and
tools against independently defined behavior contracts.

Do not put benchmark solutions, verifier shortcuts, task-specific expected
answers or benchmark-name activation tricks into skills. Do not select the
final tasks after seeing candidate gains. Freeze the candidate before accessing
confirmatory task content. Track exact and source-group overlap, derived cases,
public previews and known exposure. Public tasks and unknown training exposure
do not justify an unconditional contamination-free claim.

## Success criteria and reporting

Preregister per-suite practical effect thresholds, independent task counts,
sample sizes, comparison families, stopping rules and uncertainty calculations.
Use the official primary metric. Require both practical improvement and
statistical support against both requested baselines in the declared population.
Retain neutral, harmful and inconclusive outcomes. Repeated seeds and translated
versions of the same task are not additional independent tasks.

Preserve native scoring denominators and report the complete planned experiment
separately. In τ-Bench, an incomplete frame has no official score, and native
infrastructure errors are reported as `error_trials`. Do not alter that metric
or hide those attempts: also report planned-run completion, every failure and
missing-outcome sensitivity. Cost and token results require actual usage;
missing usage is not zero. Uncontrolled workstation timing supports no speed claim.

Publish raw native reports, exact task/image/dataset identities, intervention
digests, source exposure, seeds, failures and paired uncertainty. Generate
graphs only from admitted real results. Show official task outcomes, baseline
comparisons, uncertainty, costs and denominators. Keep engineering qualification
and source-probe counts outside efficacy plots. Claims identify the tested
models, agents, tasks and environments; finite evaluations cannot prove an
improvement for every possible model and task.
