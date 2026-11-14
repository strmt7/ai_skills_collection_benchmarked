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

The native SkillsBench verifier accepted the reference solution and rejected
an empty graph on the authors' pinned task environment. Its CTRF reward groups
35 pytest cases into six entries, so the two denominators must stay visible.
See [native SkillsBench qualification](research-skillsbench-native.md).

The [SWE-Skills-Bench archive verification](research-swe-skills-bench-archive.md)
reproduced the publisher's four paired comparisons. A separate public
development control ran an original verifier on a pinned image. It detected
a deliberately introduced syntax error, and the unchanged starting revision
already reached the cell's scoring ceiling. The result gate rejects
incomplete runs, and a second development cell qualified two-file transfer
from a closed producer into a fresh grader. The supported handoff tool also
qualified a zero-change capture and rejected a modified archive before
reconstruction. A declared skip policy binds the empty Packaging candidate's
0/11 native result to its completed capture and reconstruction receipt.
The [native grading controller](native-benchmark-controller.md) now connects
those steps through one supported entry point. The schema-2 profile verifies
declared framework and project import origins before tests. See the
[runtime-origin controls](research-native-runtime-origins.md). Model launch
and live transport qualification remain required for a matched experiment.

The Windows subject adapter now supports automatic, hash-locked dependency
installation into a fresh private profile. In the Packaging development cell,
51,498 unchanged project version tests passed inside the subject sandbox.
Its integrated edited, unchanged and interrupted controls retained 11/11,
0/11 and no score respectively. This qualifies that development path, not a
model's ability or a complete benchmark suite. The qualified profile uses pytest
9.0.3: tested newer releases reject the project's original generator parametrization
under its unchanged warnings-as-errors policy. The repository's own test
runner remains on its separately qualified version. See the
[dependency-runtime review](../artifacts/research/2026-11-11/subject-dependency-runtime/review.json).
Remaining resource and grader import boundaries, live
authentication/transport and independent matched frames still need
qualification before model launches can open.

Controlled native shells and the actual `codex exec` tool path were observed
inside the controller's job on the pinned Windows setup, including forced
parent timeouts. Separate paired writes qualified cumulative job write
accounting. See the [resource observations](../artifacts/research/2026-11-11/native-resource-observation/review.json).
The [versioned native plan](native-benchmark-controller.md) now declares and
enforces a polled write-transfer budget. Its controlled tests reject over-budget
and unmeasured execution without a score. Schema-3 plans add explicit
caller-available space reserves and bounded stopped-workspace accounting,
including caches and alternate data streams. These observations do not impose
a hard filesystem quota or establish the complete model-evaluation boundary.
The [storage review](../artifacts/research/2026-11-11/native-storage-budget/review.json)
records seven reconciled controls, including the retained failed fixture and
its independently qualified correction. These controls contain no real model
inference or evidence of comparative skill gains.

On Windows, a separate controller test used Codex CLI 0.167.1 and a scripted
loopback Responses provider. The controller ran a sandboxed PowerShell tool,
collected the exact submission and distinguished a valid submission, an
invalid one and a truncated stream. Fifteen context and isolation checks also
passed. External model transport and the full SkillsBench controller adapter
still require qualification. See the [qualification evidence](../artifacts/research/2026-11-11/benchmark-qualification/review.json).

A subsequent [authentication review](research-codex-authentication.md) confirmed
an existing ChatGPT login and a successful read-only status check in a separate
controller profile. No API key was required for those checks, and no model
request was made. Credential availability, refresh behavior, live model access
and complete runner qualification are separate requirements. The next execution
work must integrate and qualify the selected method before opening the launch gate.

## Execution priorities

Use the authors' datasets, scoring implementations and native result formats.
An integration adapter transports inputs and results; it must not rewrite the
grader, expected answers or acceptance thresholds. Preserve published version
boundaries and label partial runs explicitly.

Scripted qualification must verify native `command_execution` completion and
integer exit code 0, using `tools/_scripted_tool_control.py`, then validate the
operation's independent output files or test results. A completed CLI turn or
an echoed success marker does not prove that its tool command succeeded:
failure tracebacks can quote the marker from source. Preserve failed receipts
and explicitly revoke any conclusions contradicted by native tool status.
Also check the final structured control verdict and every declared criterion;
process exit zero cannot override a failing nested report. A retained helper
returned an earlier boolean after its final report failed. The
[claim audit](../artifacts/research/2026-11-13/qualification-claim-audit/review.json)
revokes that historical pass and preserves both original records.
This requirement applies to controlled qualification. Failed debugging commands
remain legitimate events in real model trials; their native task graders
continue to determine the score.

The [fixed-cohort preflight](../artifacts/research/2026-11-13/cohort-execution-preflight/review.json)
preserves twelve tasks with twelve enabled unit-test stages and three enabled
build checks. Five of seven publisher image manifests are verified; two Node
image references denied anonymous reads. Neither a unit-test-only adapter nor
those partial image captures admit the cohort. Current DICOM client controls
use the publisher's 300-second test timeout; the earlier 120-second diagnostic
remains historical. Qualify every declared stage and runtime before model runs.

The [native resource qualification](../artifacts/research/2026-11-13/native-project-resources/review.json)
removes fixture-sized component limits that excluded the fixed frame's original
600–900-second test stages. Two native grader profiles retain 900-second test
budgets through staging and scoring. Separate live controls verify explicit
project CPU, memory and executable-workspace quotas, plus orphan cleanup for a
2,460-second lease. Full build-stage integration and language-specific dependency
graphs remain required; passing these controls does not admit the cohort.

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

## Frozen public development selection

The [selection review](../artifacts/research/2026-11-13/swe-skills-pilot-selection/review.json)
reconciles all 98 skill records and 980 task-file references against the pinned
SWE-Skills-Bench author configuration and Git tree. It reads neither publisher
outcome tables nor task briefs, evaluator implementations or reference solutions.
The archived frame has 90 declared repository groups. The explicit cybersecurity
hold and one unresolved repository revision leave 89 groups eligible for this
metadata-only selection; that is not runtime eligibility.

The [selection receipt](../benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/selection.json)
chooses one skill/batch cell from each of 12 distinct declared repository groups.
It schedules the default, Karpathy-derived and collection conditions once per
task: 36 planned attempts. Each six-task block uses all six condition orders.
The seed is the SHA-256 of the exact pinned author configuration, independently
of result tables. This fixed development design is reproducible; it is not proof
of random, representative or semantically independent sampling.

Check its exact inputs and output without rewriting the receipt:

```powershell
python tools/select_swe_skills_tasks.py --frame artifacts/research/2026-11-11/swe-skills-bench-archive/frame.json --exclusions benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/exclusions.json --seed f658aca6273493e179b592e650341bc2cf76b1c48002633e592ab68c6cef212b --tasks 12 --output benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/selection.json --check
```

Use `./dev.ps1 python` in place of `python` for automatic isolated setup on
Windows x64. Offline validation checks the same receipt without starting an agent.

The [prospective policy](../benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/policy.json)
preserves native metrics and thresholds, every scheduled attempt and unscored
outcome, no counted retries or replacements, and explicit stopping/amendment
rules. The pilot is descriptive only. Its candidate, exact budgets, task/image/
scorer admission, model identity and complete analysis contract remain unfinished.
No model was invoked, and the launch guard remains closed. Local hashes do not
establish public preregistration timing. Public development tasks must never be
promoted to an untouched confirmatory holdout.

The selected environments' [registry metadata](../benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/environment-metadata.json)
resolves five image references to Linux/amd64 descriptors. Anonymous queries for
the two Node references returned denied/authentication-required responses; those
responses do not establish whether the images are private or absent. That
metadata capture pulled no images and created no containers. Keep those cells in the fixed cohort
while qualifying official access or a clearly recorded source-built environment;
do not silently substitute images or resample tasks. Descriptor metadata alone
does not qualify image contents, original-environment equivalence or a scorer.

The [environment feasibility review](../artifacts/research/2026-11-13/swe-environment-feasibility/review.json)
checks the documented registry flow against a public image and a missing-tag
control. Both Node references still reject anonymous manifest access. The
author's Node 20/22 scripts export local Enroot archives. A checksum-frozen
Node 22 prototype passed seven capability controls in temporary storage on the
cached Python image, including rejection by the wrong-major runtime. That
prototype leaves original-image equivalence, selected dependencies, subject tool
access and scoring unqualified. Declare and validate any source-derived route
before counted outcomes; keep all 12 selected cells and 36 scheduled attempts.

The subsequent [modern Node replay](../artifacts/research/2026-11-13/node-local-replay/review.json)
qualifies Node 26.13.1, npm/npx 11.20.0 and the maintained loader for a
checksum-bound, untagged image archive. Its publisher base layers remain exact;
the Node layer and PATH change are explicit. Two native rejection controls
prevent loading a bad digest or tagged archive. Five affected publisher-grader
regressions and the anonymous credential-selection control were repeated against
the current implementation. These are runtime and controller qualifications.
The original Node aliases remain unresolved, and complete task dependencies,
all evaluator stages and common model-trial admission remain open.

The [original build-scorer controls](../artifacts/research/2026-11-13/publisher-build-scorer/review.json)
now retain five real native command outcomes and six publisher contract checks.
The independently qualified [build-result validator](benchmark-build-results.md)
admits consistent failures and timeouts while rejecting contradictory, incomplete
or stale evidence. This does not complete the three selected project builds.
Faiss's pinned default enables GPU support, Prometheus declares Go 1.25.0 and Nx
pins pnpm 10.28.2 with an eight-way build. Actual probes record the capabilities
of the cached Python and modern-Node runtimes; the Golang image remains unprobed.
Do not disable required features or replace full source scope to obtain a pass.
Complete the original multi-stage aggregate as well as each native stage before
common trial admission; the publisher averages enabled stage scores and rounds
the aggregate to three decimal places.

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
