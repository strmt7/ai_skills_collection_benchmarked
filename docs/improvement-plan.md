# Development plan and release readiness

This collection remains experimental. Meaningful improvement over the default
agent and the Karpathy-derived baseline has not been demonstrated. No release
or tag will be created without the owner's later explicit request.

This is the controlling plan for the existing active goal. The
[machine-readable work order](../data/development_plan.json) records dependencies,
acceptance criteria and scope holds. The
[dated audit](../artifacts/research/2026-11-11/repository-state/audit.json)
preserves the observations below. Update the work order after material gates;
do not overwrite historical observations or create a separate goal.

## Verified position on 11 November 2026

The [source-bound improvement ledger](../data/improvement_ledger.json) contains
673 skills across 15 categories from 30 distinct contributing source repositories.
Its current workflow states are:

| Work stream | Complete | In progress | Pending |
| --- | ---: | ---: | ---: |
| Research | 2 | 316 | 355 |
| Revision | 5 | 53 | 615 |
| Evaluation | 0 | 12 | 661 |

There are resource inventories for 191 skills: 140 resource records are reviewed
and 1,317 remain pending. Records are scoped to skills and can overlap between
nested packages. Inventories and workflow states are not readiness percentages
or evidence that a model benefits from a skill.

Automatic isolated installation and recovery cover validation dependencies,
CocoIndex Code, Crawl4AI and the pinned benchmark CLI. At the state-audit
checkpoint, checks passed 2,925 tests with 18 skips, 75.28% coverage and typing across
316 Python files. All nine checks in that frozen batch passed; its 22,197 inputs
remained unchanged during execution. Subsequent planning changes need separate
checks. Process, credential, evaluator and storage controls retain positive and
negative fixture evidence. These are infrastructure results, not model trials.
The complete live-model boundary remains gated. See the
[latest control review](../artifacts/research/2026-11-11/native-storage-budget/review.json)
and [validation](../artifacts/research/2026-11-11/native-storage-budget/validation.json).
See [setup](../toolchains/bootstrap/README.md) and [trial methods](agent-trial-protocol.md).

Subsequent P1 work added explicit unauthenticated numeric-loopback providers,
preserving existing authenticated declarations and exact option order. Four
native controls qualified edited, unchanged, interrupted and authenticated
regression behavior; the full suite passed 2,941 tests with 18 skips. See the
[provider-authentication review](../artifacts/research/2026-11-11/native-provider-authentication/review.json).
This is a limited deterministic transport capability: no real model was invoked,
no local backend or weights were admitted, and the public launch guard stays closed.

The historical [published development checkpoint](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/5c95bcac4646c5aed06bd9aed5235cfc7985aafc)
completed 39 triggered workflows: 31 passed and eight failed. The
[retained hosted review](../artifacts/research/2026-11-10/hosted-checkpoint-review/review.json)
drives the follow-up repairs. A local pass alone did not catch interpreter
availability, Windows command resolution and quoting, upstream package drift,
or Linux type-checking errors. Hosted acceptance and the paused security gates
remain release requirements; a subsequent source revision needs its own checks.

The historical [follow-up checkpoint](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/5a51fca0e994a574820ef673a1b62e609c05f9b6)
finished all 15 triggered workflows: 13 passed and the two paused security gates
failed. Windows validation passed on a targeted rerun with 2,570 tests and 56
skips; its initial Node timeout remains an unresolved intermittent finding.
The [follow-up review](../artifacts/research/2026-11-10/hosted-repair-follow-up/review.json)
retains both attempts. A passing rerun does not establish a repair.

At the 11 November state audit, local and published main both identified
`c80f19ad60fda34b59197010ebe4fd84df5d4323`. Before this planning update, the
working tree had 112 uncommitted files: 28 modified and 84 untracked. None
changes immutable `included/skills/` mirrors. GitHub has one branch, no open
pull requests, no releases and no tag refs. All ten runs triggered on that head
are terminal: eight succeeded; [CodeQL](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/runs/42893946152)
and [Secret scan](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/runs/42893945983)
failed. Causes and fresh alert inventories were not investigated in this
overview because security work is paused. Historical alert totals are not
current counts. Ten triggered runs do not mean all 45 workflow definitions ran.
The unpublished local changes have no hosted acceptance.

Three public rulesets are active: main-only development, the tag/release hold,
and protection against deletion or history replacement of main. Classic branch
protection details remain unverified: that administrative endpoint returned
403, `Resource not accessible by integration`, for the active connector. This
specific limitation does not establish that required checks are absent or that
all GitHub APIs are blocked.

The [native benchmark plan](benchmark-execution-plan.md) supersedes the older
preflight's evaluator status. Native positive and negative scoring controls now
exist, while complete supported model transport and launch admission remain
unqualified. Preserve scoring semantics and resource ownership; do not change
the workstation's OS or bypass the public model-launch refusal.

The earlier nine matched development attempts reached a ceiling: each of the
default, Karpathy and experimental conditions passed three times. That result
does not demonstrate an advantage. Official external-suite scores for this
collection have not been established.

At that state audit there were 26 maintained overlay records, all explicitly unbenchmarked. The 34
historical packaging repairs and two experimental native-testing overlays are
different populations. Provenance copies and aliases are not additional unique
improvements. The 718 scenario templates, 18 registry methods at declared-source-
probe stage and README's 14 selected smoke adapters are not model scores.

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

The [Windows bootstrap review](../artifacts/research/2026-11-13/windows-bootstrap-runtime/review.json)
qualifies Node 26.13.1 and a compiler-free, source-bound process supervisor with
39 native setup controls. The corrected launcher passes output and output-limit
controls on both Windows CLR runtimes, including extended paths. Architecture
admission uses the runtime APIs and passes with absent or incorrect inherited
CPU variables; the earlier nested-launch failure remains unadmitted. Its maintained
builder produces the same 9,728-byte assembly twice from pinned inputs. Five
current-source controller/grader controls also pass, preserving successful,
failed-task and unscored-import outcomes. Earlier failed and interrupted
qualifications remain unadmitted. These results establish neither agent gains
nor hosted acceptance. Other deliberately versioned native workflow families
still need separate compatible-version qualification.

The [original build-scorer qualification](../artifacts/research/2026-11-13/publisher-build-scorer/review.json)
adds five native outcomes, six original-scorer contract controls and independent
build-result admission. Native evidence can now be validated from a clone;
contradictions remain unscored. Source and runtime probes identify concrete
prerequisites for the three selected build stages. Full project builds, their
controller integration and original multi-stage aggregation remain open.
The [native resource qualification](../artifacts/research/2026-11-13/native-project-resources/review.json)
also verifies explicit project quotas and preserves the frame's longer test
deadlines. Seven original-grader controls pass, including two 900-second
configurations; resource and lifecycle controls remain separate from complete
project-build admission and model efficacy.
The [current qualification index](../data/native_qualification_index.json)
binds this fresh component evidence to the exact sources superseding older
reports. Historical build and bootstrap reports stay unchanged. Unexplained
source drift, missing supersessions and changed evidence fail the index gate;
an unrelated component update need not rebuild an unchanged image.

The owner-authorized operating-policy review clarifies that maintained skill
redesign and functional testing can proceed while model-runner work remains
open. Frozen comparisons retain their original revisions; development advances
through explicitly identified snapshots. Repository-maintenance restrictions
do not become general restrictions on agents consuming skills elsewhere.
The fresh upstream-head checks match the existing community baseline and the
three previously reviewed official repositories; only the generated badge's
canonical link needed updating.

## Problems and inefficiencies

1. **The product claim remains unproved.** Packaging checks, source proofs,
   deterministic controls and coverage do not establish better agent decisions.
   The next major result must come from discriminating matched external trials.
   Do not improve static counters or build optional infrastructure instead.
2. **Skill and resource coverage is incomplete.** Review examples, scripts,
   dependencies and licenses as well as instructions. Inventories and phase
   states must not masquerade as complete research or efficacy evidence.
   The [standard-target helper controls](../artifacts/research/2026-11-13/makefile-standard-targets/review.json)
   reproduce four false successes despite the supplied regression script passing.
   Maintained guidance now requires preserving effective rules and real failure
   statuses. Four of that package's eleven resources have scoped reviews; its
   remaining guides and language cases are still open, with security work held.
3. **Private experiments have accumulated.** The private planning area contained
   139 Python scripts and 412 top-level directories. They retain useful failures
   and provenance but make replay and discovery costly. These are ignored assets,
   not tracked-repo contamination; recursive disk footprint was not measured.
   Consolidate qualified methods into maintained configurable commands. Preserve
   frozen inputs and failures; reuse admitted environments for validation batches.
4. **Documentation and delivery need consolidation.** There are 145 top-level
   documentation files and 45 workflow definitions. The previous rolling plan
   had stale counts and evaluator status. Build a revision-aware report index
   and workflow trigger/dependency map before merging or retiring anything.
   Counts alone do not prove redundancy. Keep user setup prominent and developer
   operations linked separately.
5. **The unpublished batch is large.** Review pending files with exact source
   bindings, generated outputs and newline behavior. Publish cohesive qualified
   batches; do not push merely to reduce the dirty-tree count.
6. **Runtime qualification remains a prerequisite.** Complete supported unattended
   provider transport, isolation and source-bound admission. An installed CLI,
   discovered model or successful help command does not satisfy this gate.
7. **Readiness has unresolved evidence gaps.** Hosted failures, current scanner
   totals, administrative protection details and complete Codecov upload/UI
   verification remain open. Security stays held. A passing rerun does not prove
   a flaky-test repair. Dependency maintenance qualifies whole compatible graphs.
8. **The manual is not verified.** All 154 page texts have ledger status
   `inspected_claims_unverified`; all seven attachments are inventory-only or
   partially reviewed. Of 15 shared requirements, 11 await verification and four
   are partial. Six project actions include one security deferral, four partial
   items and one open item. Verify claims independently, including relevant visual
   content and embedded materials; inspection is not acceptance.
9. **Structural review must be evidence-led.** The 316 Python modules contain
   about 63,925 lines; several tools are large. Size warrants responsibility and
   interface review, not an assumption of defects or an early cosmetic rewrite.
   Review distribution metadata, including the local `0.2.0` version and platform
   classifiers, before readiness claims. A package version is not a GitHub release.

## Ordered work packages

One development controller executes dependency-ready work. Independent research
can advance while a runtime capability is restored. Dependent benchmarks cannot
bypass gates. The approved exception permits serial isolated test subjects, not
separate development or review agents.

| Package | State and dependencies | Deliverable and acceptance gate |
| --- | --- | --- |
| P0: state and plan | Complete for this audit | Reconciled local/published state, this document and the work order. Keep observations dated. |
| P1: execution route | Active; P0 | CLI 0.167.2, source-frozen vendor catalog, 529 focused tests, 13 native metadata cases, three maintained cache controls, one late-global-instruction control, nine bootstrap controls and 3,107 full-suite passes with 18 skips. The discovered real sign-in home contains global instructions and remains ineligible. Finish supported profile isolation, recovery, fresh setup, model identity and complete admission. Keep public refusal closed. |
| P2: development experiment | Active; P0 | Source-verified metadata selection now fixes 12 declared repository groups and 36 prospective condition attempts without reading outcomes. Complete selected task/scorer admission, intervention identities, budgets, activation and the full analysis contract before counted comparisons. Selection alone is not preregistration or execution admission. |
| P3: complete skill review | Active; P0 | Evidence-backed dispositions for every skill, resource, upstream and applicable manual claim. Work in bounded batches; runtime promotion needs P1 and P2. Security-category work stays held. |
| P4: useful pilot | Pending; P1, P2 | Serial clean matched conditions, native external scoring and actual usage. Retain every attempt. A ceiling, floor or underpowered result triggers diagnosis, not superiority claims. |
| P5: iterative improvement | Pending; P4 | Transferable redesigns, routing/content/tool ablations and broader development tasks. Preserve regressions and null results. Never fit benchmark answers. |
| P6: confirm transfer | Pending; P3, P5 | Freeze final candidates and untouched confirmatory selection. Demonstrate practical, statistically supported gains against both baselines in declared model/task populations. Publish limitations. |
| P7: delivery engineering | Active; P0 | Current compatible stable graphs, isolated automatic setup, root-cause flaky-test repairs, workflow map, exact-source coverage and reproducible CI. Recheck dependency alerts without suppression. |
| P8: security work | Held; P0 | After explicit scope restoration only: paginated exact-source scanner inventories, count reconciliation, root-cause bulk remediation and verified thresholds/protection details. No suppression or guessed exceptions. |
| P9: qualified checkpoint | Pending; P7, P8 | Review exact bytes; use only the official connector to expected-head main with GitHub-assigned identity. Wait for required jobs on that commit. Repeat for cohesive batches. |
| P10: final structural refactor | Pending; P3, P5, P6, P7, P8 | Complete folder/interface/report cleanup and short end-user README after substantive work. Preserve provenance, stable interfaces or explicit migrations and old evidence. Requalify consumers. |
| P11: final readiness | Pending; P3, P6, P7, P8, P9, P10 | Reconcile requirements against the final exact revision and hosted checks. Notify the owner of readiness and limitations; create no release or tag. |

P1 has priority: finish the shortest supported qualified path to the requested
GPT-6.1 Sol high comparison through the official harness or app with the existing
sign-in. The owner ruled out providing an OpenAI API key: do not request,
provision or use one, or substitute direct OpenAI API requests for that route.
Local models provide supplementary evidence; they
cannot silently replace that target. Stop infrastructure expansion once the
necessary gate passes. P2 proceeds without inspecting held-out answers. Advance
P3 independently and P7 for concrete failures, compatibility or release needs.

The [official harness sign-in review](../artifacts/research/2026-11-11/official-harness-signin/review.json)
identified the integration mismatch: the adapter's empty `CODEX_HOME` hides the
existing sign-in. The official exec flag can ignore user configuration while
retaining native authentication storage. The initial explicit native adapter qualified
417 passing focused tests and six synthetic native controls, including original
11-case positive/unchanged grading and subject denial of store access. Native
testing exposed global AGENTS discovery despite the config flag; admission now
rejects those entries without changing the user's profile. See the
[controller review](../artifacts/research/2026-11-11/native-signin-controller/review.json).
The full suite passed 2,994 tests with 18 skips across 22,205 unchanged frozen
inputs. Skipped platform/scanner checks are not claimed as passing.
Finish shared-profile/refresh stability, remaining context channels, real model
identity and source-bound launch admission. These controls do not open the gate.

Four subsequent [native lifecycle components](../artifacts/research/2026-11-11/native-signin-lifecycle/review.json)
qualify synthetic refresh persistence, generation-conflict preservation,
rejection and timeout accounting. Cancellation can leave the authority's
simulated grant changed while the local cache is unchanged. Establish explicit
official preflight and interruption semantics; an account response or cached
status alone is insufficient refresh proof. At that lifecycle checkpoint, the 404 functional source files
covered by the earlier full-suite snapshot remained byte-identical; those
controls add component evidence rather than another full-suite or model score.

The [metadata-readiness entrypoint](../artifacts/research/2026-11-11/native-account-readiness/review.json)
combined account, authenticated quota and model metadata without exporting
tokens or starting a model turn. That round passed 11 native cases and 470 focused tests;
the full suite passed 3,048 tests with 18 skips and 22,211 unchanged frozen inputs.
App-server honors the selected profile while isolated exec ignores user config.
Qualify configuration concordance and remaining profile/cache channels before
using this component for full launch admission. Metadata eligibility does not
prove model effectiveness or complete this package.

The [configuration-readiness review](../artifacts/research/2026-11-11/native-configuration-readiness/review.json)
adds before/after configuration and origin-version checks, rejects explicit
catalog substitutions and retains a native omitted-field regression. All 13
metadata controls and 494 focused tests passed; the new full suite passed
3,072 tests with 18 skips and 22,211 unchanged frozen inputs. Two scripted
catalog-isolation controls also passed: isolated exec omitted the profile
marker, while deliberate flag removal exposed it and withheld the result.
The unchanged positive task still scored zero; these are infrastructure controls.
Their scope does not establish every shared-cache channel or real-account model
identity. The public model-launch refusal remains closed.

The [13 November catalog review](../artifacts/research/2026-11-13/native-vendor-catalog/review.json)
supersedes the CLI pin with stable 0.167.2. Native controls reproduced a separate
matching-cache leak during catalog refresh failure. Both maintained runners now
use the same source-verified vendor catalog, with before/after digest checks and
portable archived command evidence. Nine bootstrap controls include automatic
catalog recovery. Validation passed 529 focused tests, typing across 324 Python
files, 13 native metadata cases and 3,107 full-suite tests with 18 skips. The full
suite's 22,214 frozen inputs remained unchanged; line coverage was 75.75%.

The actual sign-in home remains ineligible because it contains global
instructions. Presence-only discovery did not read credentials or modify user
files. Official source and one generated-profile late-file control show that
global instructions still load despite ignored configuration and a zero project
budget. Admission rejection remains necessary and shared-profile concurrency
remains unqualified. Do not move user files, copy credentials or erase vendor
base instructions. Continue independent P2/P3 work while establishing a supported
isolation route. No real model, skill-gain or commercial-readiness claim follows
from these infrastructure results; the public launch guard stays closed.

## Every-skill research and redesign loop

The [13 November C++ review](../artifacts/research/2026-11-13/makefile-cpp/review.json)
adds a [maintained Makefile overlay](../included/improved/skills/makefile-generator-cpp/SKILL.md)
after independently reproducing lost compiler flags during linking and a test
target that succeeded without tests. All six Linux compiler controls passed
with GNU Make 4.3 and a source-verified build of 4.4.1;
Windows file-generation controls passed with four compiler-dependent skips.
That checkpoint contained 27 maintained overlay records, all unbenchmarked for agent efficacy.
The source package's 11 resources are inventoried; remaining guides, other
language cases and held security guidance prevent whole-skill completion.

The [current E2E review](../artifacts/research/2026-11-13/e2e-readiness/review.json)
adds a maintained candidate after seven live Windows browser controls. The exact
TypeScript example passes on a ready polling page and fails at the intended
assertion when readiness is absent, retaining a valid trace and screenshot.
The original example is unchanged in the checked current upstream; the broader
source update is not adopted by this observation. Earlier response-ordering
repairs remain historical evidence. There are now 28 maintained overlay records,
all unbenchmarked for agent efficacy. Remaining application, browser and CI
claims still need qualification; security work remains held and real model
launches remain unqualified.

Start with coding, testing, agent infrastructure and retrieval. Process bounded
batches, normally five to eight skills or fewer for resource-heavy packages.
Preserve every skill ID and resource disposition in the ledger. Batch size
controls context and resources; it never justifies skipping difficult entries.

1. Inventory all original files, dependencies, licenses, source pins and limits.
   Read supporting resources; compare upstream changes and current primary sources.
2. Define intended outcomes and general failure hypotheses. Record independent
   task/evaluator provenance outside the exact skill text. Research is not a score.
3. Design the smallest transferable improvement. Preserve mirrors; use attributable
   overlays with original provenance, explicit activation and qualified portable setup.
4. Verify readiness with meaningful positive and negative controls. Functional
   success is not efficacy.
5. Compare against both baselines on independent development tasks. Separate
   instruction, routing and tool effects; retain costs, regressions and missing data.
6. Promote supported scopes, reopen evidence after material changes and feed
   general findings into later batches. Reserve untouched tasks for P6. Unchanged
   skills need justified dispositions, not arbitrary rewrites.

All category populations stay accounted for: Azure/cloud SDKs (178), science
(148), communication/productivity (59), security (57, held), OMERO/lab (46),
DevOps (40), coding/refactoring (30), creative/design (30), game/mobile (25),
testing (19), retrieval (16), documents/spreadsheets (12), agent infrastructure
(8), frontend/browser (3) and finance (2). The sum is 673. These labels are
shortened; operations use exact ledger IDs/categories. Prior cross-repository
inspiration must remain generic, cannot replace independent tasks and does not
authorize new work on other owner repositories.

## Benchmark design and reporting

Use three matched conditions: B0, the same agent without collection instructions;
BK, that agent with the pinned community Karpathy-derived baseline; and BC, the
candidate skills with declared activation. The source is
`multica-ai/andrej-karpathy-skills` (formerly `forrestchang/andrej-karpathy-skills`),
not a Karpathy-owned repository, pinned at
`2c606141936f1eeef17fa3043a72095b4765b9c2`. Reverify contributing upstreams
during their reviews.

Keep model, reasoning setting, ordinary tools, task input, environment, budgets
and evaluator constant except for the intervention. Name any separate tool-bundle
experiment and its ablations. Use clean serial contexts under the approved
exception; never share development memory, earlier answers or personal profiles.
Qualify runner and grader on public controls before real subjects.

Prioritize skill-focused SkillsBench and SWE-Skills-Bench methods, then compatible
SWE-bench repository tasks and Terminal-Bench terminal tasks. Extend relevant
domains through the existing registry, including BrowserGym/WebArena, WorkArena,
BFCL tool use and scientific tasks. Confirm versions, licenses, native scorers,
environment needs and coverage before selection. Registry entries, popularity
and smoke checks are not suite scores. Breadth cannot replace enough independent
tasks within each claimed population.

Use pilot variance and feasibility to specify confirmatory allocation and practical
thresholds before accessing holdout content. Preserve official metrics and scoring
denominators; report paired uncertainty clustered by independent task, multiplicity
handling and sensitivity analyses. Repeated seeds are not new independent tasks.
Report native scoring and the whole planned experiment separately, including
setup errors, cancellations, timeouts, missing outcomes and harmful effects.
Never silently drop failed pairs.

Quality gain is the primary requested result; lower cost alone does not satisfy
it. Token, cache and cost comparisons require actual provider measurements;
missing usage is not zero. Workstation timing requires controlled host context
and repeated measurements. Generate plots from validated artifacts with counts,
uncertainty, versions and raw-evidence links. Packaging checks, source proofs and
fixture controls never enter agent win rates. Finite experiments support declared
models/tasks, not a promise that every possible model improves.

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

Use maintained setup commands for missing qualified dependencies in owned isolated
caches on the declared OS/architecture. Never assume host packages, paths, cached
credentials or administrator access. Reuse admitted environments in frozen batches.
Keep Python formatting at 120 columns. Audit whole runtime/build graphs against
current stable compatible releases and document compatibility pins.

Verify the coverage producer, revision, upload receipt, service processing and UI
independently. A badge or local percentage does not prove Codecov accepted a report.
Do not claim the tracked-lines "deactivated" state resolved without live evidence.
A rerun alone does not establish a flaky-test root-cause repair.

The manual ledger remains authoritative for S01-S15 and AISC-01-AISC-06. Finish
relevant page, attachment and visual checks, verify against current sources and
this repository, then record adoption, justified non-applicability or a scope hold.
Do not copy recommendations as facts or modify other repositories.

The work order maps requirements R1-R12 to packages P0-P11. Recheck mappings after
scope changes. Advance only from inspected exact-source evidence; a completed
package does not complete the broader goal. Security/scanner and history work stay
held, preventing full readiness. Publication uses the official connector and
GitHub-assigned identities; this update authorizes no history rewrite.

Immediate sequence: P1 qualification, P2 preregistration, P4 pilot, then P5
iteration alongside P3 review. Execute this plan within the existing active goal.

Readiness requires evidence-backed dispositions for every catalog entry and
resource, independently validated applicable skills, meaningful held-out
advantages against both requested baselines, current installation/dependency
and workflow acceptance, and closure of required findings. One successful task,
coverage percentage, static audit or source probe is insufficient. There is no
defensible overall completion percentage or date while those requirements remain open.
