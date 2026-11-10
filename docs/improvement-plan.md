# Release readiness and work plan

This collection remains experimental. Meaningful improvement over the default
agent and the Karpathy-derived baseline has not been demonstrated. No release
or tag will be created without the owner's later explicit request.

## Progress as of 10 November 2026

The [source-bound improvement ledger](../data/improvement_ledger.json) contains
673 skills across 15 categories. Its current workflow states are:

| Work stream | Complete | In progress | Pending |
| --- | ---: | ---: | ---: |
| Research | 1 | 317 | 355 |
| Revision | 5 | 53 | 615 |
| Evaluation | 0 | 12 | 661 |

There are resource inventories for 190 skills: 138 resource records are reviewed
and 1,317 remain pending. Records are scoped to skills and can overlap between
nested packages. Inventories and workflow states are not readiness percentages
or evidence that a model benefits from a skill.

Automatic isolated installation and recovery cover validation dependencies,
CocoIndex Code, Crawl4AI and the pinned benchmark CLI. Local engineering checks
have passed 2,608 tests, 20 nonpaused repository gates, 32 setup controls and
native context/tool controls. The shared controller's nine positive and negative
cases and Python interruption cleanup have passed model-free controls. These
are infrastructure results. The complete live-model boundary remains gated.
See [setup](../toolchains/bootstrap/README.md) and [trial methods](agent-trial-protocol.md).

The [published development checkpoint](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/5c95bcac4646c5aed06bd9aed5235cfc7985aafc)
completed 39 triggered workflows: 31 passed and eight failed. The
[retained hosted review](../artifacts/research/2026-11-10/hosted-checkpoint-review/review.json)
drives the follow-up repairs. A local pass alone did not catch interpreter
availability, Windows command resolution and quoting, upstream package drift,
or Linux type-checking errors. Hosted acceptance and the paused security gates
remain release requirements; a subsequent source revision needs its own checks.

The [follow-up checkpoint](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/5a51fca0e994a574820ef673a1b62e609c05f9b6)
finished all 15 triggered workflows: 13 passed and the two paused security gates
failed. Windows validation passed on a targeted rerun with 2,570 tests and 56
skips; its initial Node timeout remains an unresolved intermittent finding.
The [follow-up review](../artifacts/research/2026-11-10/hosted-repair-follow-up/review.json)
retains both attempts. A passing rerun does not establish a repair.

The [native SkillsBench preflight](research-skillsbench-native.md) admitted a
public development package and the official evaluator without changing either.
Windows command validation is blocked by an upstream POSIX-only import. Separate
dependency graphs resolve, but native oracle/verifier and model execution remain
unqualified. The next environment must preserve the authors' scoring semantics,
have explicit resource ownership and leave the workstation's OS unchanged.

The earlier nine matched development attempts reached a ceiling: each of the
default, Karpathy and experimental conditions passed three times. That result
does not demonstrate an advantage. Official external-suite scores for this
collection have not been established.

The [10 November upstream observation](../artifacts/research/2026-11-10/karpathy-baseline-head.json)
found that the Karpathy-inspired source still matches the pinned baseline
commit. That observation does not complete review of the other upstreams or
establish the baseline's quality.

The supplied implementation manual has 154 pages and seven embedded files.
All extracted page texts have been inspected; claim verification, embedded-file
review and relevant visual checks remain open. Follow its
[review ledger](../artifacts/research/2026-11-03/implementation-manual-review/ledger.json).
Its recommendations remain claims to verify, and the owner's 120-character
Python limit and current repository scope remain controlling.

## Ordered execution

1. **Publish a carefully verified development checkpoint.** Review every pending
   file, dependency graph, generated output and provenance boundary. Validate
   the exact bytes to publish, including Git's line-ending behavior. Commit
   through the approved GitHub connector, advance only `main` with an expected
   head, then wait for hosted workflows on that commit. Preserve rollback
   identities and avoid frequent small pushes. A checkpoint is not a release.
2. **Integrate native external scoring.** Execute the
   [independent benchmark plan](benchmark-execution-plan.md). Prioritize direct
   skill studies, repository engineering and terminal tasks, then broaden
   coverage across scientific, browser, tool-use and other relevant suites.
   Qualify authors' scorers on public development controls and the actual model
   transport before any new model call. Registry resolution and adapter smoke
   checks do not satisfy this step.
3. **Complete each skill's research.** Process bounded non-security categories
   through the ledger without skipping entries or resources. Read original
   instructions, examples, scripts, dependencies and licenses; compare pinned
   upstreams with current official sources and record remaining gaps. Use
   `tools/manage_improvement_ledger.py --check --json` and its category/skill
   inventory operations. An inventory is not a completed review.
4. **Redesign maintained skills and tools.** Infer general failure mechanisms
   from independent development evidence and current primary research. Apply
   the [improvement method](skill-improvement-method.md) to every applicable
   skill and tool. Preserve immutable mirrors; implement attributable overlays
   with exact original provenance, verified installation, supported runtime
   behavior and independent regression checks. Reopen evidence after relevant
   upstream or source changes. Keep mirroring, repair and evaluation loops separate.
5. **Measure and iterate on development tasks.** Freeze matched baseline,
   Karpathy and candidate conditions, task inputs, budgets, routing, sample
   allocation and analysis. Use native external outcomes, not locally invented
   success scores. Retain every attempt, setup error, timeout, negative effect
   and missing measurement. Improve transferable behavior rather than fit
   benchmark answers, and evaluate individual skills as well as bundles.
6. **Confirm meaningful transfer.** Freeze final candidates and untouched
   confirmatory selection before inspecting task content. Test multiple model
   families, agents, repositories and task families with practical thresholds,
   independent task counts, paired uncertainty and multiplicity control.
   Publish neutral or negative results and precise scope limits. Show gains
   only where the actual evidence supports them.
7. **Close delivery requirements.** Qualify current compatible stable tool and
   package graphs, source licenses, installation paths, generated artifacts and
   workflows on the final revision. Complete the manual's remaining verified
   actions. Resolve dependency, DeepSource and code-scanning findings without
   suppressing them, under the owner's active scope. Security/scanner and
   history remediation are currently paused and remain release dependencies;
   dependency maintenance is authorized. Capture current counts instead of
   repeating stale alert totals.
8. **Perform the final repository refactor and presentation pass.** After the
   substantive skill, tool and evaluation requirements are addressed, map
   maintained code, immutable sources, generated data, historical evidence,
   CLI/JSON contracts and consumers. Consolidate real duplication, simplify
   ownership and workflow setup, preserve supported interfaces and update
   callers and validators together. Preserve historical bytes and failures;
   a digest does not authorize rewriting the evidence it identifies. Finish
   the short end-user README and navigation, link contributor material
   separately, and verify links, packaged resources, deterministic generation,
   behavior and hosted checks after the migration. Revalidate any affected
   benchmark comparison and generate showcase graphs only from real results.

## Operating and release constraints

Use one development controller and serial isolated experimental subjects under
the [benchmark policy](benchmark-subject-policy.md). Keep mandatory tools,
source-bound receipts and [host resource lifecycle rules](../AGENTS.md#process-and-host-resource-lifecycle).
Bound processes, concurrency and output; clean up owned children on success,
failure and cancellation. Preserve unrelated applications and other tasks.
Use the declared Windows x64 local target and qualify separate benchmark
environments explicitly. Do not change the host operating system or assume
preinstalled applications.

All development stays on `main`; no development branches, dependency-update PRs,
releases or tags. Work only in this repository. Public upstreams and disposable
external benchmark inputs do not authorize changes to the owner's other repos.

Readiness requires evidence-backed dispositions for every catalog entry and
resource, independently validated applicable skills, meaningful held-out
advantages against both requested baselines, current installation/dependency
and workflow acceptance, and closure of required findings. One successful task,
coverage percentage, static audit or source probe is insufficient. There is no
defensible overall completion percentage or date while those requirements remain open.
