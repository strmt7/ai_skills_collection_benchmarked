# Choosing benchmarks for skill effectiveness

No measured advantage of this collection over the default agent or the
Karpathy-derived baseline has been established. Published leaderboard results
describe their tested systems; they are not results for these skills.

This 9 November 2026 review expands the registry from 14 to 18 methods and
refreshes two source locations. The [source observations](../artifacts/research/2026-11-09/benchmark-expansion/sources.json)
retain capture identities, failures and review limits. Six selected repositories
resolved to immutable commits in new source probes. No model, native task suite
or benchmark verifier was run by those probes.

## Which comparisons are useful

| Method | What it can test | Admission limits here |
| --- | --- | --- |
| [SkillsBench 1.1](https://www.skillsbench.ai/) | Paired skill effects across professional domains; the published release has 87 tasks. | Freeze task, skill and harness versions separately. A one-sided leaderboard entry cannot estimate a skill effect. |
| [SWE-Skills-Bench, paper v2](https://arxiv.org/abs/2603.15401v2) | Individual skill utility on repository requirements, paired across agent/model configurations. | The paper links to [ControllableModel](https://github.com/ControllableModel/SWE-Skills-Bench); the former GeniusHTX URL returned HTTP 404. Audit task/oracle independence before admitting cases to our efficacy claims. |
| [WebDev-Skills-Bench study](https://arxiv.org/abs/2608.23067v1) | Routing, prompt-length effects and skill-component ablations in web development. | Methodology reference only: the abstract was reviewed; the full paper, code and executable suite have not been qualified here. |
| [SWE-Bench Pro V2](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2) | Longer repository changes with issue-resolution and regression checks. | The V2 announcement specifies 642 public tasks and clean-image regrading. The page also retains legacy numbers; pin the actual split. Public tasks are not private holdouts. |
| [DeepSWE 1.1](https://deepswe.datacurve.ai/blog/deepswe-v1-1) | Original long-horizon tasks, with committed patches regraded in a fresh environment and named test outcomes. | Review verifier validity and complete inventories independently. Repository resolution does not qualify its images, data or tests. Do not substitute v1 scores. |
| [Terminal-Bench 4.1](https://github.com/harbor-framework/terminal-bench/releases/tag/v4.1.0) | Terminal workflows and resource-sensitive tool use. | The release API identifies 4.1.0 as the latest published stable release observed here, superseding the researched 4.0 announcement. Full and CPU-only datasets have different denominators. |
| [WorkArena / WorkArena++](https://github.com/ServiceNow/WorkArena) | Enterprise browser workflows, composed planning and application-state outcomes. | Requires approved ServiceNow instances and a qualified BrowserGym stack. No instance was accessed. Its documented oracle demo is not agent performance. |
| [ScienceAgentBench](https://osu-nlp-group.github.io/ScienceAgentBench/) | Scientific programming and discipline-specific output correctness. | Review data licenses, dependency environments and scientific oracles. Program execution alone does not establish scientific validity. |

Other registered methods answer narrower questions: function-calling checks
assess tool-call behavior, browser frameworks provide environments, and ML
competitions assess particular outputs. Do not average their scores into an
unqualified universal skill score.

## What changes in our experiments

The current SWE-Skills-Bench paper reports little aggregate benefit, while the
WebDev study reports model-dependent losses and substantial token overhead.
These are author-reported findings, not independent reproductions. They support
testing whether a skill should activate. See the [redesign method](skill-improvement-method.md).

Future development experiments must distinguish:

1. **Content:** matched no-skill, pinned Karpathy-derived and candidate conditions.
2. **Routing:** natural discovery versus explicit injection, including tasks
   where the correct choice is not to activate the skill.
3. **Context cost:** length-matched irrelevant controls and component ablations.
   Preserve tools and auxiliary-file access unless that access is the declared
   intervention.
4. **Transfer:** other repositories, task families, supported environments and
   model/harness configurations. Keep population-specific effects separate;
   repeated attempts are not additional independent tasks.
5. **Reliability:** complete denominators, regressions, setup failures, timeouts,
   missing usage, partial outcomes and negative effects; paired uncertainty,
   task-level variation and costs alongside the primary outcome.

Choose practical effect thresholds, sample sizes, comparison families and
stopping rules before outcomes. Record incidental exposure: public previews,
task names, demonstrations and annotated examples were encountered during
this research. Treat those public materials as development-exposed; never use
them as proof of untouched evaluation. No task solutions or reference patches
were sought for candidate tuning, and none were imported into skill guidance.

Freeze candidates before holdout execution. Later changes require a new
candidate and new untouched evaluation material. The existing refusal to launch
model trials remains until runner/grader integration is qualified; that work
is deferred while security work is paused. This review authorizes no release.

## Reproducing source checks

`python tools/evaluate_external_benchmark_methods.py --check --json` checks
generated registry data and retained source-probe bundles offline. Historical
observations are checked against their own declarations; selected current
observations must match current definitions. This does not run an external
benchmark. New observations require a new run name and explicit observation
timestamp; previous evidence must remain unchanged.
