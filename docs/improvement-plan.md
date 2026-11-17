# Development plan and release readiness

The collection is under development. It has not demonstrated a meaningful
advantage over the same agent without skills or over the pinned community
Karpathy-derived baseline. It is not ready for a commercial release. Do not
create a release or tag; the owner will decide publication separately.

This is the controlling implementation plan for the existing active goal,
refreshed on **17 November 2026**. The [active work order](../data/development_plan.json)
retains requirements R1–R12, packages P0–P11, dependencies and scope holds.
The [dated assessment](../artifacts/research/2026-11-17/repository-state/audit.json)
records the evidence and limitations. Previous observations remain historical;
the previous edition is recoverable at
[commit 8be77acf](https://github.com/strmt7/ai_skills_collection_benchmarked/blob/8be77acf11261b918f6380426dc8cdece82c1b9e/docs/improvement-plan.md).
This plan authorizes neither a second goal nor another development agent.

## Current repository overview

### Product, evidence and architecture

The useful product is a searchable collection of task-focused skill packages,
with source provenance, explicit maintained overlays and evidence about their
supported behavior. The engineering system imports pinned public sources,
generates the catalog and entrypoints, records reviews, prepares isolated tools,
and evaluates artifacts. These functions must remain distinguishable to users.

| Area | Present state | What remains to establish |
| --- | --- | --- |
| Catalog | 673 skills, 15 categories, 30 contributing repositories; 80 selected entries | Complete source, resource, currentness and supported-scope dispositions for every entry |
| Locked sources | Original mirrors and deterministic catalog generation | Review all upstream changes; inclusion does not certify quality or safety |
| Maintained candidates | 28 records in the maintained-overlay manifest | Whole-skill readiness and independent model benefit; an overlay record is not a measured improvement |
| Packaging repairs | 34 repair-manifest records plus two separate native-testing experiments | Keep packaging repair, functional correctness and model efficacy separate |
| Scenario definitions | 718 templates | Independent executable tasks, original evaluators and actual runs |
| Benchmark discovery | 18 registry methods at declared-source-probe stage | Qualified adapters and suite executions; historical smoke results are not suite scores |
| Model evidence | An earlier one-task, nine-attempt comparison reached a ceiling: all three conditions passed three times | Discriminating, paired development results and untouched confirmation |
| New development experiment | Frozen 12-task frame, 36 prospective condition attempts, zero counted attempts | Complete runtime graphs, model transport, isolation, admission and prospective analysis |
| Setup and ownership | Isolated managed environments, native process ownership and component controls | Complete supported fresh-host, relocation, recovery and dependency-graph qualification |
| Quality | Extensive tests, typing, deterministic validators and hosted controls | All applicable workflows accepted on the published revision, unresolved integration failures and held findings closed |
| Release | Explicit hold; no release authorized | All readiness gates, then an owner decision |

The current ledger has **2 complete / 316 in-progress / 355 pending research**
records, **5 / 53 / 615 revision** records, and **0 / 12 / 661 evaluation** records.
These are workflow states with limited recorded scopes, not completion or quality
percentages. There are resource inventories for **192 skills**, comprising
**1,468 per-skill resource records: 152 reviewed and 1,316 pending**. Nested
packages can share physical resources. Another **481 skills have no recorded
resource inventory**; that does not establish that their packages contain no
supporting files.

The tracked inventory on published head
[8be77acf](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/8be77acf11261b918f6380426dc8cdece82c1b9e)
contains 22,693 files: 18,916 under included/, 2,255 under artifacts/, 835 under
docs/, 191 under benchmarks/, 160 under tools/ and 197 under tests/. There are
146 top-level documentation files and 46 workflow definitions. The explicitly
counted maintained Python scopes—tools/, tests/ and the agent-effectiveness
graders—contain 357 modules and 71,957 lines in the observed working snapshot.
Other mirrored and overlay programs are outside that module count. File size
and counts are review inputs; they do not demonstrate defects or duplication.

| Boundary | Responsibilities and invariants |
| --- | --- |
| data/source_lock.json → catalog generator | Select pinned public inputs and deterministic allowed transformations; never tune mirrored instructions for benchmarks |
| included/skills/ | Immutable upstream baseline, including documented deficiencies |
| included/agent-ready/ and generated catalog pages | Portable routing and source metadata; generated outputs must remain synchronized |
| included/repaired/ | Explicit packaging/runtime repairs with original provenance; retain the original mirror |
| included/improved/ | Maintained candidates, research rationale, supporting resources and declared limits |
| data/improvement_ledger.json | Exact per-skill source signatures, research/revision/evaluation state and evidence |
| benchmarks/, evaluators/ and tools/ | Task selection, execution, native scoring and result validation; keep oracles outside subject access |
| toolchains/ and dev.ps1 | Verified isolated setup, bounded process ownership and actual public command contracts |
| artifacts/ and data/native_qualification_index.json | Dated observations and exact current/historical source qualification, never a substitute for model outcomes |
| docs/installation.md and README | End-user discovery, requirements, setup and honest evidence; developer operations remain linked separately |

The package metadata currently declares version 0.2.0 with empty setuptools
package and module lists. This is not evidence of a published release or a wheel
containing an installed application. Define the intended source-clone, package
and optional-distribution contracts before commercial claims. No root LICENSE
file was found in the tracked inventory. Preserve upstream licenses and notices;
resolve licensing of maintained code and aggregate distribution explicitly.
Do not infer permission to relicense upstream material.

### Exact-revision quality observations

All **16** workflow runs observed for 8be77acf are terminal: **10 succeeded and
6 failed**. This is not a claim that all 46 workflow definitions ran. Failures
were CocoIndex setup-output binding, Crawl4AI setup-output binding, the offline
stable-action check, LLVM freshness, the code-scanning budget and secret-history
scanning. The first four are ordinary P7 integration work. Scanner remediation
remains held under P8.

The preceding local publication qualification passed all 19 nonheld checks,
including 3,459 tests with 18 expected skips, on unchanged inputs. Hosted runs
nevertheless found a real launcher regression: console writes bypassed
PowerShell assignments, pipelines and redirection. The follow-up reproduces six
consumer failures and passes all nine frontend ownership/stream controls after
repair. Actual public CocoIndex and Crawl4AI commands also return valid JSON
through pipelines while reusing their admitted profiles. These focused results
do not establish hosted acceptance of the follow-up revision.

The follow-up also resolves actions/setup-go v7.1.0 to its official commit.
LLVM 23.1.6 Windows assets appeared during this round. The verified archive and
matching compiler/runtime pass all 11 unchanged native outcomes after the
runner stages its matching DLL app-locally. The original 266-character DLL-path
startup failure is retained. These are native component controls, not AI scores.
The Windows compiler controls still use discovered MSVC/Windows SDK prerequisites;
this does not establish automatic setup of those prerequisites on a fresh host.

Codecov's API reports the exact 8be77acf commit complete, with 70.19% coverage,
158 files and 19,958 tracked lines. Reconcile its metric with the exact uploaded
reports and local representation. The tracked-lines “deactivated” UI has not
been verified resolved. Coverage measures exercised tooling code, not skill
intelligence. DeepSource's exact-commit check was skipped with **“Analysis quota
is exhausted.”** This does not establish a current findings total or an API/auth
block. The CodeQL budget reported 86 open alerts against a limit of two; its
snapshot was not atomic. Do not treat that observation as a new reconciled
inventory or an approved exception list.

Fresh public GitHub reads confirm main as the only branch, no tag refs, no open
pull requests and no releases. Three active public rulesets restrict non-main
branch creation/update, all tag creation/update, and main deletion/history
replacement. Their observed rules have no bypass actors. Classic protection
and the complete effective required-check policy still require verification;
a prior administrative read was denied to the integration. Never extrapolate
that endpoint limitation to all API access or attribute it to the owner.

The community baseline's fresh head still matches
2c606141936f1eeef17fa3043a72095b4765b9c2 in
[multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills),
formerly forrestchang/andrej-karpathy-skills. This is a community Karpathy-inspired
repository, not a repository owned by Karpathy. That observation does not verify
all 30 contributing upstreams or prove baseline quality.

### Principal problems and avoidable costs

1. **No demonstrated capability advantage.** Infrastructure, static counters,
   source proofs and coverage cannot answer the product's central question.
   Prioritize a qualified discriminating external comparison over optional runner
   features, decorative graphs or broader registries without executions.
2. **Incomplete per-skill and resource work.** Many reviews are partial; supporting
   programs, dependencies, examples, licenses and failure behavior need their own
   dispositions. An inventory is not a review, and a passing example is not a
   complete skill evaluation.
3. **Counted model trials remain unqualified.** The scripted native packaging
   boundary passed its context and execution controls. The live Qwen3 1.7B
   probe loaded the pinned CPU model at a 16,384-token context. The official
   harness completed the turn and delivered one command, which exited 1 because
   the model chose a placeholder script path. The required file was absent.
   Retain the raw trace and failed, unscored attempt. The earlier gpt-oss:20b run
   timed out after 180.089 seconds with a missing required `cmd` field. Its later
   preflights also stopped before inference. The requested official signed-in
   GPT-6.1 Sol high route awaits a clean, isolated authenticated context.
4. **Original task graphs are incomplete.** Node file-loader metadata access,
   Go, Faiss/CUDA, Nx/pnpm and complete original build/test/collection stages need
   qualification. An AMD GPU does not establish CUDA compatibility. Preserve the
   frozen frame rather than drop inconvenient tasks or alter their scoring.
5. **Qualification has missed real callers.** A successful native capture did not
   prove PowerShell pipeline behavior. Test the actual public consumer contract,
   including interruption, before broad suites and publication. Preserve both
   failing and passing source identities.
6. **Excess repeated I/O and private orchestration.** Earlier inventory and
   publication helpers scanned too widely. Keep ignored research out of navigation,
   use explicit tracked paths, reuse admitted caches and stage only reviewed files.
   Consolidate recurring qualified methods; retain failures and frozen inputs.
   A long check needs a durable start identity and terminal result, not an ambiguous
   progress file. This is targeted reliability work, not a new general framework.
7. **Documentation and workflow sprawl.** Map consumers, triggers, required checks,
   generators, public entrypoints and report precedence before removing or merging.
   Chronological status appendices have allowed old counts and pins to look current.
   The final refactor must establish one current plan and an indexed evidence archive.
8. **Distribution and licensing are unresolved.** Source-clone behavior, installed
   payload, platform promises, provider licenses and root-project terms need explicit
   acceptance. Do not label metadata installation as application installation.
9. **The supplied manual is not verified.** Its original 8,182,434-byte PDF hash
   was rechecked: e47cd7084b51ba5b8d8ef0f6b1cb9cb0812d90b46af328caec55705ed1b2304e.
   All 154 extracted pages remain inspected_claims_unverified; seven attachments
   are inventory-only or partial. Of 15 shared requirements, 11 are pending and
   four partial; six AISC actions include a held security item and an open efficacy
   item. Inspect relevant visuals and embedded claims; never adopt recommendations
   merely because they appear in the document.
10. **Commercial acceptance is blocked.** Per-skill closure, independent gains,
    complete portability/dependency graphs, hosted acceptance, coverage reconciliation,
    distribution terms and held security work remain. No credible completion
    percentage or release date follows from present counts.

## Execution order and state transitions

One development controller runs dependency-ready work. Benchmark subjects are
serial isolated test conditions under the approved exception, never delegated
developers or reviewers. Normal development retains all mandatory tools. OpenAI
runs use the official app/harness with existing sign-in only; no OpenAI API key,
credential copying or direct OpenAI request is permitted.

The critical path for each benchmark study is its P1 execution route and P2
task qualification, followed by P4 development runs, P5 iteration and P6
confirmation. A study can proceed when its own dependencies pass. An unresolved
Faiss, Go or Node environment in the fixed SWE-Skills-Bench pilot does not hold
up another independently selected study. P6 requires P3 acceptance for the
candidate and resources it evaluates. P11 still requires the full catalog
disposition, final refactor, delivery checks and closure of held work. P9 repeats
for cohesive qualified batches.

| Package | Current state | Dependencies | Exit condition |
| --- | --- | --- | --- |
| P0: state and plan | Complete for the assessment | None | Source-bound overview and synchronized active work order |
| P1: model execution | Active | P0 | Qualified real model-to-tool-to-artifact route, isolation, cleanup and admission |
| P2: development protocol | Active | P0 | Each study's native task graphs and frozen comparison and analysis contract. The original pilot retains all 12 graphs. |
| P3: every-skill redesign | Active | P0 | Complete accounted-for research/resource/revision dispositions; evaluation still needs its gates |
| P4: development comparisons | Pending | P1 and P2 for each study | Complete matched attempts and native scoring for the declared population |
| P5: iterative improvement | Pending | P4 | Transferable revisions, controlled ablations and independent development transfer |
| P6: confirmation | Pending | P3 for the candidate and P5 for the study | Untouched, frozen, adequately powered confirmation against both baselines |
| P7: delivery engineering | Active | P0 | Current compatible graphs, supported installation/recovery, coverage and hosted quality |
| P8: security/scanners | Held | P0 plus restored owner scope | Reconciled inventories and verified authorized remediation; no suppression |
| P9: publication checkpoint | Active, repeatable | P0 and applicable batch gates | Verified connector publication and every triggered hosted result retained |
| P10: final refactor | Pending | P3, P5, P6, P7, P8 | Coherent final structure, migrations, archived evidence and short end-user README |
| P11: readiness audit | Pending | P3, P6, P7, P8, P9, P10 | Exact-revision requirement audit and candid readiness report; no release |

A task changes state only when its acceptance evidence exists and is inspected.
A partial success advances the recorded substep, not the whole package. Missing
access, incompatible environments and interrupted commands remain explicit;
never substitute assumptions, a passing rerun or a reduced denominator. Work on
an independent ready package while a genuine external capability is unavailable.
Do not wait on a supposed publisher job without an actual job identity.

### Immediate work sequence

1. The launcher stream repair, app-local LLVM deployment and setup-go pin
   passed 20 local gates and were published in
   [b20d0e1c](https://github.com/strmt7/ai_skills_collection_benchmarked/commit/b20d0e1c6a1195a1784ca21290fbf141bec078c1).
   All 19 observed runs on this revision finished, including two later
   scheduled runs. Seventeen passed. CodeQL and Secret scan failed under the
   current hold. Codecov processed this revision at 70.19%.
2. Keep coverage explicit in full measured runs and use focused tests during
   development. Bind context qualification to its runtime dependencies. Retain
   the current native replay and prior independent verification-skill controls
   under their exact source identities.
3. Preserve the smaller model's failed live probe and its four passing scripted
   controls. Qualify the approved signed-in route in a clean context. Resolve
   runtime and collection defects independently of whether a model solves a task.
4. Continue the original twelve runtime graphs and the separately scoped
   SkillsBench v1.1 build-recovery study. The two selected public task IDs are
   `fix-build-agentops` and `fix-build-google-auto`. Their publisher bytes and
   task and scorer admission remain part of P2. Keep this frame outside
   untouched confirmation.
5. Execute each P4 study when its own P1/P2 evidence passes. Let independent
   development evidence guide general revisions and a frozen confirmation study.

## P1 — qualify one complete model-execution route

**Purpose:** make a real, isolated official agent perform an actual tool action,
collect its artifact and terminate cleanly. Metadata probes are insufficient.

1. **P1.1: freeze the diagnostic boundary.** Record the official CLI version,
   source commit, executable digest, requested/reported model, reasoning setting,
   model catalog, backend identity, actual local weights digest where available,
   context, tool schema and resource graph. Keep requested GPT-6.1 Sol high and
   supplementary local-model results distinct. Do not demand unavailable private
   weight hashes for proprietary providers or infer identity from a model's prose.
2. **P1.2: qualify native traces without inference.** The pinned official CLI
   exposes CODEX_ROLLOUT_TRACE_ROOT. Use independent scripted peers to check valid
   and malformed tool arguments, tracing disabled/enabled, cancellation, truncation,
   size limits and cleanup. Keep traces controller-owned and inaccessible to the
   subject; preserve ephemeral execution and avoid external telemetry. Establish
   what the trace actually records before relying on it. Preserve complete failures.
3. **P1.3: specify a new public calibration prospectively.** Before launch, fix
   prompt, expected artifact, model/reasoning, deadline, tool schema and pass/fail
   criteria independently of candidate skills. Require an actual executed command,
   expected artifact bytes, completed turn and consistent native event trail.
   An echoed call or reasoned plan is not execution. Retain parser/provider errors;
   do not unwrap malformed calls or add favorable prompt hints to hide a defect.
4. **P1.4: prove the full resource envelope.** Retain the 16 GiB local backend,
   2 GiB coding subject, declared enclosing command allowance and 28 GiB available
   RAM preflight where that generation profile requires them. Verify nested job
   limits, cancellation, output caps and listener cleanup from actual observations.
   The corrected enclosing budget is qualified separately from successful inference.
   Never kill the user's unrelated Ollama or change the workstation operating system.
5. **P1.5: finish signed-in official-route isolation.** Establish a supported
   app/harness configuration that does not import personal instructions, history,
   skills, caches or configuration into the subject. Test matching and stale
   catalog cases and late-created global instructions. Do not move personal files,
   copy credential stores, remove vendor base instructions or weaken the no-skills
   condition. A local-model pass does not close this requested route.
6. **P1.6: qualify end-to-end execution and collection.** Exercise meaningful
   positive, task-failure, malformed-call, timeout, interrupted-controller, missing
   artifact and collection-boundary controls using the same maintained launcher.
   Prove editing, build/test invocation, artifact collection and independent grader
   visibility. Check source digests before/after and actual owned-job termination.
7. **P1.7: admit only the proved scope.** Produce a clone-validatable admission
   artifact binding environment, controls and source identities. Keep the public
   refusal until the complete gate passes. Afterward stop optional infrastructure
   expansion and run the planned development comparison.

**Exit evidence:** native traces and controls, real calibration artifact and events,
requested/reported model identity, isolation proof, full source-bound admission,
resource/cleanup receipts and a tested replay command. No efficacy claim follows.

## P2 — qualify each study and freeze its experiment

1. **P2.1: preserve the frame.** Retain the original 12 task identities, selection
   receipt, source commits and 36 prospective B0/BK/BC attempts. Preserve earlier
   declarations and failed preflights. Mark the current frame development-only;
   it is not untouched confirmation or a completed preregistration. Never backdate
   registration, substitute easier tasks or drop unsupported members.
2. **P2.2: complete every runtime graph.** Inventory the declared runtime,
   interpreter/compiler, package manager, registry/archive inputs, lockfiles,
   build/test commands, licenses, hardware, network and resource requirements for
   each selected task. Qualify Windows paths and actual native command resolution.
   Finish Node file-module loading, Go, Faiss/CUDA and Nx/pnpm specifically;
   distinguish supported external grading environments from changes to the host OS.
3. **P2.3: preserve original scoring.** Integrate every original build/test stage,
   public scoring formula and aggregation rule. Verify individual pytest cases,
   grouped CTRF outcomes and suite denominators independently; case counts are not
   interchangeable with grouped scores. Keep original time budgets and longer
   project quotas. Do not replace a native evaluator with a convenient local proxy.
4. **P2.4: qualify scorer/collector controls.** Run independently authored known
   success, known task failure, partial result, malformed/missing report,
   contradictory evidence, import failure and interruption controls. Prove the
   expected trigger and stage. Infrastructure failures remain unscored; native
   task failures remain task failures. Keep subject changes away from verifiers.
5. **P2.5: freeze conditions and activation.** B0 is the same agent without
   collection instructions; BK adds the pinned community Karpathy baseline; BC
   adds the declared candidate package and routing. Keep ordinary capabilities,
   environments and budgets equal. Declare trigger selection, manual versus
   automatic activation, installed-tool policy, interventions and order allocation.
   Measure a tool bundle in a separate ablation, not as unexplained instruction gain.
6. **P2.6: register analysis before outcomes.** Specify estimand, native primary
   metrics, task population, pairing/randomized serial order, repetitions,
   feasibility criteria, exclusions, missingness policy, multiplicity, practical
   effect criteria and stopping rules. For the pilot, emphasize feasibility and
   effect uncertainty; twelve tasks do not automatically provide adequate power.
   Timestamp and hash the exact protocol and candidate versions.
7. **P2.7: admit the declared study.** Validate its included task/runtime/scorer
   graphs, isolation, resource limits, cleanup and budget feasibility together.
   Use the same frozen evidence boundaries for each external method. Qualify a
   newly selected independent study in its own versioned declaration. Its
   selection policy must be fixed before candidate outcomes and retain projected
   coverage and excluded capabilities. Report it with that study's denominator.
   The original 12-task pilot's admission and results remain separate.

**Exit evidence:** a frozen population, task/runtime manifests, native positive
and negative scorer results, original aggregation proof, frozen conditions,
prospective analysis and complete admission for that study. The original pilot
requires all twelve task/runtime manifests. A different study's result cannot
close that requirement.

## P3 — research and redesign every skill and maintained tool

### Common per-skill contract

Process bounded batches, normally five to eight entries and fewer for large
resource packages. Batch boundaries control context, never coverage. Keep all
673 IDs and their source signatures in the ledger; retain the held security
population. A changed source invalidates affected conclusions, not unrelated
completed work.

1. **P3.1: inventory the entire package.** Enumerate instructions, scripts,
   references, assets, examples, nested skill boundaries, dependencies, licenses,
   external services and generated files. Record shared physical resources without
   counting them as independent evidence. For apparent zero-resource packages,
   retain an actual source-tree inventory proving that scoped observation.
2. **P3.2: verify upstream and current sources.** Resolve each contributing
   repository's actual current head and stable release policy, compare changed
   files with the lock, inspect primary documentation and qualify compatibility.
   Distinguish Karpathy's statements, community interpretation and this repository's
   adaptation. Record URLs, versions, dates, digests, failures and scope. Do not
   import every latest commit without review or treat search snippets as research.
3. **P3.3: define a general behavior contract first.** Record intended users,
   activation/non-activation cases, inputs, outputs, prerequisites, boundaries,
   failure modes and independent functional checks before designing a candidate.
   Evaluators and expected answers must not derive from the exact skill text.
   Generic software specifications and independent task requirements are inputs;
   benchmark solutions and verifier details are not candidate design material.
4. **P3.4: review every resource.** Check runnable examples, real exit status,
   failure propagation, dependency APIs, data formats, state changes, portability,
   disposal and license attribution. Preserve scoped findings. A prose review
   cannot close an unexecuted program, and one working example cannot close all
   language/platform variants. Keep unsupported or externally unavailable cases
   explicit instead of inventing a pass.
5. **P3.5: write the smallest transferable candidate.** Preserve included/skills/.
   Use maintained or repaired overlays with exact original provenance. Give clear
   triggers, a compact decision procedure, stopping/verification rules, practical
   examples and limitations. Put detailed references and resources behind explicit
   links; avoid blanket verbosity, repository-owner paths and benchmark-ID logic.
6. **P3.6: qualify the real user path.** Test meaningful successes and failures
   through documented entrypoints, including consumer pipelines where applicable.
   Exercise actual installed contents, dependencies and representative inputs.
   Prove declared OS/architecture support and safe missing-dependency setup for
   the operation. Preserve resource/lifecycle observations and negative controls.
7. **P3.7: record a justified disposition.** Accept unchanged source when evidence
   supports it; otherwise retain a maintained candidate, an explicit limitation,
   a failed check or a scope hold. Do not rewrite every skill mechanically.
   Research and functional readiness remain separate from model efficacy.
8. **P3.8: evaluate and revisit.** Freeze candidates before their declared model
   comparison. Use P4/P5 development evidence for general failure mechanisms,
   not answers. Changed candidates receive new identities; invalidate only affected
   claims. Close evaluation only for the tested task/model/agent scope.

### Complete category work queue

| Category | Skills | Inventoried packages | Research complete | Revision complete | Evaluation complete |
| --- | ---: | ---: | ---: | ---: | ---: |
| Agent infrastructure & skill creation | 8 | 1 | 1 | 0 | 0 |
| Cloud, Azure & Microsoft SDKs | 178 | 0 | 0 | 0 | 0 |
| Coding, refactoring & repository automation | 30 | 11 | 0 | 3 | 0 |
| Communication, productivity & support | 59 | 0 | 0 | 0 | 0 |
| Creative, media & design | 30 | 1 | 1 | 0 | 0 |
| DevOps, cloud & operations | 40 | 2 | 0 | 0 | 0 |
| Documents, spreadsheets & presentations | 12 | 0 | 0 | 0 | 0 |
| Finance, commerce & forecasting | 2 | 2 | 0 | 0 | 0 |
| Frontend, UI & browser automation | 3 | 3 | 0 | 2 | 0 |
| Game, mobile & visual QA | 25 | 2 | 0 | 0 | 0 |
| OMERO, Django, Docker & lab infrastructure | 46 | 2 | 0 | 0 | 0 |
| Science, research & data analysis | 148 | 148 | 0 | 0 | 0 |
| Search, retrieval & web automation | 16 | 0 | 0 | 0 | 0 |
| Security, compliance & risk | 57 | 1 | 0 | 0 | 0 |
| Testing, QA & benchmarking | 19 | 19 | 0 | 0 | 0 |

The current category counts are workload denominators, not effectiveness claims.
Security-affecting work in the 57-entry security category remains held; other
held material encountered in mixed packages also receives an explicit deferral.
Never omit held entries to make overall progress look complete.

### Category-specific research and independent checks

| Category family | Research and redesign focus | Independent functional evidence before model claims |
| --- | --- | --- |
| Agent infrastructure and skill creation | Activation precision, progressive disclosure, capability requirements, context budgets and artifact contracts | Relevant/irrelevant activation controls; actual generated package loads; tool and file outcomes rather than self-reported compliance |
| Coding, refactoring and repository automation | Preserve program semantics, build rules, error propagation, dependency APIs and maintainable changes | Real compiler/test failures propagate; unchanged behavior and public interfaces survive; representative supported language cases execute |
| Testing, QA and benchmarking | Test oracle independence, discriminating assertions, subprocess status and metric semantics | Seeded defects fail at the intended assertion; clean controls pass; missing reports, empty suites and contradictory results cannot pass |
| Retrieval and web automation | Current-root indexing, source freshness, relevant retrieval, actual page scope and explicit external failures | Stale/wrong-root inputs reject; returned spans match live source; native crawls retain substantive content and honest failures |
| Frontend and browser automation | Readiness, race conditions, accessibility, browser lifecycle and user-visible outcomes | Real browser positive/negative readiness cases, trace/screenshot validity, console checks and cleanup; no sleep-only success criteria |
| Cloud, Azure and Microsoft SDKs | Stable API contracts, pagination, cancellation, required configuration and credential-free qualification | SDK compilation/type checking plus owned local protocol/service controls; qualify live-service behavior only when actually exercised |
| DevOps, cloud and operations | Declarative config, idempotence, failure handling, recovery and bounded side effects | Disposable environment apply/reapply/recovery controls; validate workflow caller inputs and real failure exits |
| OMERO, Django, Docker and laboratory infrastructure | Supported runtime/API contracts, application lifecycle, data integrity and service dependencies | Owned disposable service/data fixtures, migration/restart/readback tests and actual supported environment receipts |
| Science, research and data analysis | Numerical assumptions, units, input schema, missingness, data provenance and method validity | Independent mathematical/reference controls, boundary datasets, exact output checks or justified tolerances; distinguish API readiness from scientific validity |
| Documents, spreadsheets and presentations | File validity, formulas/layout, interoperability and usable output | Open/render/round-trip representative artifacts; verify values and visual requirements independently; never use file existence alone |
| Creative, media and design | Intent preservation, asset rights, deterministic transformations where applicable and reviewable output | Format/decoding controls, before/after checks and independent visual or human rubric where an objective oracle is unavailable |
| Game, mobile and visual QA | State progression, input/layout behavior, platform compatibility and measured resource use | Real supported runtime/device controls, failure reproduction, frame/input checks and justified performance measurements |
| Communication, productivity and support | Correct context, audience, verifiable facts, action boundaries and concise usable output | Independent task rubrics, wrong-context/irrelevant-trigger controls and factual/action verification; do not substitute length for quality |
| Finance, commerce and forecasting | Data/time provenance, units, costs, leakage and uncertainty | Independent calculations and temporal validation; no profitability or decision-quality claim from a functional example |
| Security, compliance and risk | Preserve accounting and existing findings while scope is held | No redesign/scanner remediation under the hold; define authorized verification only after scope restoration |

### Interoperability and tool redesign

Apply the [Agent Skills specification](https://agentskills.io/specification)
against each maintained package's intended interface. Its metadata and
progressive-disclosure conventions are useful interoperability requirements;
conformance does not demonstrate effectiveness. Keep descriptions specific and
resources optional until needed. Do not inject this repository's development
holds or publication rules into unrelated downstream projects.

Inventory every maintained tool by public entrypoint, consumer, dependency graph,
state/resources and required evidence. Repair concrete failures before broad
refactoring. Test actual shell/object-stream consumers, not only visible output;
exercise native wire consumers rather than relying on generated type schemas.
Apply the same general-purpose and independence rules to tools and instructions.
No candidate may contain a benchmark answer, reference patch, benchmark-ID branch
or verifier-specific exception.

**Exit evidence:** every catalog/resource disposition is accounted for, all
adopted changes have provenance and appropriate functional checks, upstream and
manual claims are resolved or explicitly held, and efficacy states remain tied
to actual admitted model evidence. A valid unchanged disposition is allowed;
an unexplained pending entry is not release-ready.

## P4 — execute a discriminating development pilot

1. Freeze the admitted P1/P2 implementation, candidate artifacts and native
   scorer identities. Verify actual source bytes immediately before each attempt.
2. Execute the declared serial order in fresh isolated contexts. Do not share
   previous attempts, developer memory, tool traces or private grader material.
   Keep ordinary agent tools and budgets matched across B0, BK and BC.
3. Retain every planned attempt's event stream, usage, submission, environment,
   elapsed time, resource observations, exit/cancellation and collection result.
   Grade through the original independent scorer. Do not convert harness errors
   into model failures or silent exclusions; report both native-score and
   experiment-completion denominators.
4. Validate artifact integrity, actual condition activation and grouped scoring
   independently. Check missing outcomes, contamination and protocol deviations
   before estimating an effect. Preserve failed pairs and replacement rules.
5. Report the paired quality difference against both baselines, task-level
   uncertainty, cost/latency observations, regressions and task heterogeneity.
   Repetitions on the same task are not new independent tasks. Missing provider
   usage is unknown, not zero tokens or zero cost.
6. Diagnose ceiling, floor, low power or transport failure honestly. Keep the
   original frame intact and its result visible. A new development frame may be
   declared prospectively for a justified general coverage gap; it must not
   erase unfavorable outcomes or masquerade as untouched confirmation.

**Exit evidence:** complete attempt accounting and validated original scores,
scientific feasibility/effect report and documented general failure mechanisms.
A null or ceiling result can complete the pilot; it cannot establish superiority.

## P5 — iterate from general failures and test transfer

1. Classify development failures into skill activation, reasoning/decision
   guidance, missing domain knowledge, tool/API behavior, environment or scoring.
   Preserve ambiguity when evidence cannot distinguish causes.
2. Link each proposed revision to a general behavior contract and primary source.
   Author independent reproductions before changing guidance. Do not inspect or
   import benchmark solutions, reference patches or private verifier logic.
3. Revise maintained overlays and tools in cohesive scoped batches. Retain prior
   candidates and exact evidence. Re-run affected native/functional regressions,
   package validation and publication gates without altering upstream mirrors.
4. Run declared ablations separating routing, instruction content and tool bundle.
   Match budgets and ordinary capabilities. Include irrelevant-skill controls
   where needed to detect distraction or context overhead.
5. Repeat matched development comparisons at separately declared candidate
   revisions. Retain all earlier results; never combine changing candidates into
   one pass rate. Check new independent development tasks for transfer before
   freezing confirmation.
6. Select a candidate using a documented objective that prioritizes quality,
   practical reliability and bounded cost. Stop revising for effects inside
   noise; a favorable seed or token reduction alone is insufficient. Record null,
   negative and domain-specific effects as supported limits.

**Exit evidence:** source-bound general improvements, ablation/transfer results,
regression accounting and a frozen final candidate ready for P6 selection.

## P6 — confirm meaningful gains on untouched material

1. Define the exact claim population: task domains, supported skill scopes,
   model families/configurations, agent harnesses and operating environments.
   Finite experiments cannot prove improvement for every possible model or agent.
   The requested GPT-6.1 Sol high official-route comparison remains required;
   supplementary local results must be named as such.
2. Use pilot feasibility and variance to determine adequate independent-task
   allocation and repetitions. Document a practically meaningful minimum effect
   per native primary metric and justify it from user impact, not observed favorable
   confirmation outcomes. Freeze thresholds, power assumptions, multiplicity,
   uncertainty, clustering, missingness and stopping rules before holdout access.
3. Select confirmation tasks independently of candidate text and development
   outcomes. Record all previous benchmark/task exposure, including incidental
   public homepage task summaries from research. Previously examined material
   cannot be called untouched. Freeze selection receipt, candidate versions,
   environments and analysis before opening task content.
4. Execute serial matched B0/BK/BC conditions with qualified native evaluation.
   Evaluate more than one model and agent harness before making cross-model or
   cross-agent benefit claims. If only one qualified configuration is accessible,
   publish that bounded scope and leave broader claims unestablished.
5. Require quality improvement against **both** baselines under the declared
   practical and statistical criteria, with acceptable regressions and costs.
   Report task/cluster-level paired intervals and appropriate exact/bootstrap or
   other justified methods; seeds do not inflate the independent sample size.
   An inadequate or unfavorable result reopens development rather than shifting
   thresholds, dropping tasks or tuning the same holdout.
6. Generate plots only from validated real artifacts. Show native resolution or
   quality, paired changes/uncertainty, per-domain heterogeneity, failure categories,
   wall time and measured usage where available. Name models, harnesses, budgets,
   versions and denominators; distinguish unknown cost and host-noisy timing.

**Exit evidence:** registered untouched study, complete validated runs, practical
and statistical support against both baselines, no concealed regressions and
scope-correct public claims. Changed candidates require new untouched evaluation.

## P7 — complete delivery, dependencies, coverage and workflows

1. **P7.1: close the current public-contract defects.** Keep the six-failure
   launcher reproduction, nine passing repaired controls and two actual provider
   pipeline observations. Complete source/index freshness, full nonheld checks
   and exact-revision hosted acceptance. Preserve LLVM loader and setup-go
   observations. Do not equate one green rerun with an explained repair.
2. **P7.2: inventory all dependency graphs.** Cover root runtime/test/lint/reports,
   build backend, bootstrap Python/Git/Node/CLI, mandatory providers/models/browser,
   maintained overlays and each native workflow. Record direct/transitive packages,
   source URLs, licenses, hashes, platform constraints and qualification owners.
   Latest means newest qualified compatible stable graph, with an observation date;
   not a floating untested pin or a claim every package was checked today.
3. **P7.3: update whole compatible graphs.** Use current official releases and
   package APIs, verify complete artifacts and installed contents, then exercise
   actual imports, entrypoints and affected native workflows. Keep failed new
   versions and compatibility floors explicit. Recheck Dependabot alerts through
   the authorized official access; fixing a dependency requires runtime/install
   qualification, not suppressing its alert. Keep automatic update PRs disabled.
4. **P7.4: prove declared portability.** Test a fresh supported Windows x64
   account/cache, relocated clone/cache, spaces and relevant path boundaries,
   missing host Python/Node/Git/browser, incompatible host tools, unavailable
   downloads, offline reuse and concurrent installation recovery. No global
   packages, PATH/profile/registry changes, administrator assumption or OS switch.
   Missing declared dependencies must provision safely in owned caches; document
   and resolve remaining MSVC/SDK prerequisites before claiming that operation's
   fresh-host automatic setup. Agent-neutral package use must not require this
   development harness.
5. **P7.5: complete process and resource lifecycle.** Test first-hop death,
   cancellation and nested jobs as well as ordinary return. Bound memory, child
   count, I/O, deadlines and listeners; verify no owned processes after cleanup.
   Keep diagnostic outputs from interrupted runs and preserve unrelated apps.
   Record initial source identity durably before long checks, then final identity,
   so interruption does not leave apparently reusable but unbound evidence.
6. **P7.6: reconcile coverage.** Bind each required coverage report to exact source,
   runtime, producer and test family; verify aggregation and missing-report refusal.
   Validate upload receipts and Codecov processing for the published commit,
   reconcile line/branch/partial definitions and exclusions, and inspect the
   tracked-lines UI through official available access. Keep the generated Codecov
   badge synchronized. Coverage is a maintenance diagnostic, never skill efficacy;
   do not add mirrored implementation tests or exclusions to inflate it.
7. **P7.7: map and qualify workflows.** For each of 46 definitions, record triggers,
   paths, permissions, action identities, runtime graphs, artifacts, consumers,
   schedules, required-check status and explicit release-disable state. Validate
   reusable caller inputs and actual output streams. Exercise scheduled/manual
   latest-compatible canaries, not only locked matrix jobs. Requalify changes on
   their actual Windows/Linux environments without changing the workstation OS.
8. **P7.8: resolve delivery governance.** Define source-clone and installed-package
   contracts, intended users/platforms, maintained-code license and retained
   upstream notices. Admit package payload/module contents before installation.
   Inspect effective main protections and required checks through available
   official reads; distinguish public rulesets from administrative endpoints.
   No hardcoded contributor identity or newly authorized history rewrite.

**Exit evidence:** a complete dependency/workflow map, latest-compatible qualified
graphs, fresh/relocated/recovery demonstrations, reconciled coverage and service
state, supported distribution terms and exact-revision hosted acceptance.

## P8 — held security and scanner work

This package remains **held**. Read-only monitoring does not authorize scanner,
security-category or history remediation. Do not change exclusions, thresholds,
findings or history to turn held checks green. The following is a contingent
implementation plan for scope restoration, not permission to execute it now.

1. Retrieve complete official paginated finding inventories with native pages,
   cursor/end conditions, counts, analyzer/category identity, commit/run/config
   bindings and timestamps. For DeepSource, distinguish ordinary GitHub App
   analysis, OIDC report upload and GraphQL finding access. A report-upload
   credential policy does not establish finding-query access. Verify current
   official methods; preserve the observed quota-skipped check without guessing
   a findings total or silently changing a paid plan.
2. Reconcile inventory totals and categories against the service UI/API. If a
   complete inventory cannot be retrieved, preserve exact errors and work from
   retrievable batches without claiming completeness. Do not attribute failures
   to the user without evidence.
3. Group findings by root mechanism, source ownership, affected generated paths,
   real versus false-positive behavior and regression risk. Keep immutable mirrors
   intact; use authorized upstream updates or explicit maintained repair boundaries
   instead of rewriting audited originals or hiding analyzer coverage.
4. Reproduce representative mechanisms, implement complete maintainable repairs
   and test affected consumers and regressions. Reconcile every original finding's
   disposition. An analyzer-wide disappearance after configuration change is not
   remediation. Do not suppress alerts or create guessed exceptions.
5. Verify the actual DeepSource/code-scanning gate configuration and effective
   protections. The intended tolerance—zero DeepSource issues and only explicitly
   justified unavoidable code-scanning exceptions—needs exact alert identities,
   owner policy and current evidence. Never silently substitute a numerical
   allowance for adjudicated findings or trust an old cross-repository recollection.
6. Run complete local/hosted checks on the exact repaired commit, page the fresh
   inventories again and prove reconciliation. Keep remaining findings explicit;
   any unsatisfied required gate blocks P10/P11 readiness.

**Exit evidence after scope restoration:** original/final reconciled inventories,
source-bound root-cause repairs, genuine regression evidence, approved explicit
residual dispositions and effective failing gates. None is established by this plan.

## P9 — publish cohesive verified checkpoints

1. Freeze a reviewable batch: explicit file list, source/output identities,
   intended behavior, native evidence, failures and affected workflows. Keep
   originals and required negative evidence; avoid sweeping unrelated cleanup.
2. Run the full applicable local nonheld gates from [CONTRIBUTING](../CONTRIBUTING.md),
   including lint/format, both mypy platforms, full bounded tests, compile,
   catalog, static/risk freshness, mirror admission, ledger/overlay/lock checks,
   mandatory-tool execution receipt and native qualification-index validation.
   Preserve security-held gates as held, never claimed passes. Freeze all inputs
   through completion and re-run affected checks after relevant changes.
3. Prepare an explicit private index from the verified parent and stage only
   reviewed paths. Verify qualified bytes against prepared Git blobs and tree;
   preserve the real index. Avoid full-tree add operations over ignored research.
   Check the changed payload for real/provider-shaped credentials before sending.
4. Use only the authenticated official GitHub connector to create the tree and
   commit. Let GitHub assign identity; do not set an author/committer/co-author.
   Verify tree, ordered parents and attribution, then advance main with an
   expected-head lease and no force. A rejected lease requires fresh inspection.
5. Verify remote main and synchronize the local checkout/cache without creating
   local commits or pushing through another transport. Confirm source bytes and
   real-index state are preserved. Do not claim a connector commit is signed
   unless its verification actually reports that.
6. Enumerate and wait for every triggered workflow to finish, following pagination
   and rerun identities. Preserve individual job failures and artifacts. A missing
   path-filtered workflow is not a pass. Repair ordinary failures through the next
   cohesive qualified batch; retain held failures and their release implications.
7. Update this work order, report only meaningful changes, and audit owned process,
   service, task and listener cleanup. Do not create a branch, PR, tag, release,
   persistent monitor or separate development session.

**Exit evidence per batch:** qualified exact bytes, connector commit/ref readback,
identity/tree/parent checks, all terminal hosted outcomes and bounded cleanup.
P9 is repeatable and does not imply the whole repository is ready.

## P10 — final complete refactor and end-user documentation

Begin this final pass only after substantive P3/P5/P6/P7/P8 acceptance. Necessary
local defect repairs before then remain scoped repairs, not the promised final
whole-repository refactor.

1. Build a responsibility and consumer graph for generators, schemas, validators,
   runners, public commands, overlays, report indexes and workflows. Identify real
   duplication, cycles, competing authorities and missing contracts from evidence.
2. Choose the smallest coherent final layout. Separate immutable inputs,
   maintained candidates, runtime tooling, benchmark adapters, executable tests,
   current user documentation and historical evidence. Preserve stable interfaces
   or supply explicit migration/compatibility tests for actual consumers.
3. Split or consolidate large modules only where responsibilities justify it.
   Keep deterministic generator behavior, canonical hashes, public parser/main
   contracts and native scoring semantics. Do not perform a mechanical rewrite
   merely because a module has many lines.
4. Archive superseded reports through a revision-aware index. Keep failures,
   original inputs, licenses and evidence links recoverable. Remove only proven
   redundant/generated/disposable material with verified replacements; never
   delete inconvenient benchmark or scanner evidence.
5. Rewrite README as a short end-user path: what the collection does, supported
   scopes, honest measured benefit, choose/install/use a skill, requirements,
   limitations and links. Generate the badge block through its maintained tool.
   Put contributor and agent development details in linked developer documents.
6. Requalify end-user installation/use, every affected generator and native
   consumer, documentation links, full local gates and all applicable workflows
   on the exact final layout. Compare pre/post artifact identities and outcomes;
   preserve deliberate migrations explicitly.

**Exit evidence:** justified final architecture, migration compatibility,
reproducible unchanged contracts, indexed historical evidence and clear tested
end-user instructions. Structure alone does not repair missing capability proof.

## P11 — exact-revision readiness evaluation, without releasing

1. Reconcile every R1–R12 requirement against actual P-package outputs, every
   catalog/resource disposition and manual S01–S15/AISC-01–AISC-06 outcome. Record
   adoption, verified non-applicability or a real unresolved/held requirement.
2. Verify candidate/source/upstream/version identities, distribution licenses,
   automatic setup and supported host/agent scopes. Recheck dependency and hosted
   observations for the final revision; an old green commit is not final acceptance.
3. Audit independent confirmation, both baseline comparisons, practical/statistical
   thresholds, contamination, missing attempts, adverse effects and claim scope.
   Independently recompute report tables/graphs from validated raw artifacts.
4. Verify all required workflows terminal/successful, findings reconciled under
   authorized scope, coverage processing/UI understood, protections effective and
   owned processes/services/tasks cleaned up. Record exact exceptions and limits.
5. Give the owner a readiness report with explicit blockers and evidence. If
   everything required passes, state ready for the owner's release decision.
   **Do not create a release or tag, re-enable the release workflow or publish a
   package as a consequence of this audit.** A package version is not authorization.

## Manual verification and requirement traceability

The [manual review ledger](../artifacts/research/2026-11-03/implementation-manual-review/ledger.json)
remains authoritative for individual claims. Verify all 154 pages and seven
attachments, relevant rendered diagrams/tables, archive-member relationships and
embedded currentness claims against live source and current primary documentation.
Preserve the supplied document as evidence, never as unquestioned instructions.
Continue ordinary claim verification under P3/P7; record security deferrals under
P8. Prior cross-repository inspiration remains historical read-only context and
never authorizes new changes to another owner repository or owner-specific skills.

| Requirement | Operational coverage |
| --- | --- |
| R1 upstream and current compatible stable tools | P1 identities; P3 per-source review; P7 complete graphs and canaries |
| R2 every skill and resource | P3 exact-ID/resource accounting and category queue |
| R3 transferable redesign with immutable originals | P3 contracts/overlays; P5 evidence-driven iteration |
| R4 meaningful default and Karpathy gains | P1/P2 admission; P4/P5 development; P6 confirmation |
| R5 generic cross-repository inspiration | P3 portable contracts; no other repository mutations |
| R6 final refactor and short user README | P10 after substantive prerequisites |
| R7 host/install/agent independence and safe setup | P1/P3 actual consumers; P7 fresh/relocated/dependency qualification |
| R8 quality, workflows, coverage, dependencies and findings | P7; held P8; P9 exact-revision acceptance; P11 reconciliation |
| R9 bounded host resources and efficient work | P1/P7 lifecycle controls; P9 scoped preparation and cleanup |
| R10 every applicable manual claim | P3/P7 ledger verification; held P8; P11 traceability audit |
| R11 main, connector attribution and protections | P7 governance; P9 publication; P11 fresh audit |
| R12 honest science, provenance and limits | All packages; especially P2/P4/P5/P6/P11 |

## Research basis and limits

The current methodology review used retained native Crawl4AI captures of
[SkillsBench](https://www.skillsbench.ai/), the
[Agent Skills specification](https://agentskills.io/specification),
[SWE-bench evaluation](https://www.swebench.com/SWE-bench/guides/evaluation/)
and the [Harbor framework](https://github.com/harbor-framework/harbor/blob/main/README.md).
SkillsBench directly studies skill use; SWE-bench evaluates generated patches
against repository tests; Harbor supplies benchmark/agent environment integration.
These are complementary methods, not evidence that this collection has run them
or that any is a universal certification. Benchmark versions and official metrics
must be pinned for execution.

Use the existing 18-method registry to evaluate coverage and feasibility:
skill-focused SkillsBench/SWE-Skills-Bench/Skill-Bench; repository and terminal
methods such as SWE-bench and Terminal-Bench; browser/enterprise methods such as
BrowserGym, WebArena, WorkArena and OSWorld; tool use through BFCL; and relevant
scientific/ML methods. Verify every method's actual source, license, environment,
scorer and current version before admission. Do not average incompatible metrics,
claim a suite score from an adapter smoke check, or select benchmarks for favorable
public leaderboard outcomes. Greater breadth needs enough independent tasks
within each claimed population, not merely more benchmark names.

The current overview is an evidence-based assessment and executable plan, not
completion of its steps. Run it within the existing goal, use concise progress
updates, preserve source-bound receipts and failures, and refresh state after
material gates. The next valuable milestone is a qualified discriminating model
comparison—not a release, a larger static counter or a claim of universal gain.
