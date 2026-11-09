# Release readiness and work plan

This collection is experimental. It is not ready for a commercial release:
most skills have not completed evaluation, and measured improvement over the
default agent or the Karpathy baseline has not been established. A release or
tag will be created only if the owner later requests one.

## Current state

On 3 November 2026 the [improvement ledger](../data/improvement_ledger.json)
recorded 673 skills: research was complete for one, in progress for 317 and
pending for 355; revision was complete for five, in progress for 52 and
pending for 616; evaluation was in progress for 12 and pending for 661. On
2 November, 188 skills had resource inventories, containing 130 reviewed
and 1,317 pending resource records. These are tracking states, not a percentage
of release readiness. For current counts, run `python tools/manage_improvement_ledger.py
--check --json`.
The scientific category now has 148 skill-level resource inventories, with
1,266 resource records pending review and five marked reviewed. File records
are scoped to each skill and may overlap between nested packages. Transient
`.git` and `__pycache__` directories follow the catalog hash boundary and are
not source resources. Inventorying a file does not review or evaluate it.

The supplied 27 October implementation manual has 154 pages and seven
embedded files. Its [review ledger](../artifacts/research/2026-11-03/implementation-manual-review/ledger.json)
tracks extraction, partial inspection and unresolved actions; most of the
manual remains to be reviewed. Its internal hashes establish byte consistency,
not the correctness of its claims. Ruff, mypy and the main offline test matrix
use a checked, hashed developer lock. A separate scheduled and manually
dispatched matrix resolves the latest compatible test dependencies. Exact-commit
hosted qualification and the scheduled canary remain part of the evidence needed
for this change.
The owner's 120-character Python limit and prohibition on working on other
repositories take precedence over conflicting recommendations in the manual.
Security-related actions remain paused.

The 9 November reviews bring the inspected-page count to 100 of 154. The
common-standard batch records 47 passing local controls and limited
mappings for independent oracles, coverage validation, dependency direction and
versioned evidence. These four shared requirements remain only partially
checked; page inspection is not claim verification. The proposed embedded
closure validator has not been executed or adopted, and other repositories
were not accessed for this review.

The [expanded benchmark review](benchmark-expansion.md) covers direct skill
studies and broader engineering, terminal, enterprise-browser and scientific
methods. The [redesign method](skill-improvement-method.md) applies to every
skill and maintained tool. It requires generalizable improvements, independent
contracts, exposure tracking and honest neutral or negative results, and
prohibits benchmark-answer fitting. These documents do not complete the
remaining per-skill work or establish an agent advantage.

To add pending resource records for another category, first validate the ledger
and mirrors, then run `python tools/manage_improvement_ledger.py
--inventory-category "<exact category name>"`. Existing inventories and review
states are preserved; source changes invalidate associated work through the
ledger's synchronization rules. To inventory selected skills without processing
the rest of a category, use `--inventory-skill "<skill id>"` and repeat that
option for each selected ID. Neither command marks resources as reviewed.

The first nine matched development attempts scored three passes in each of the
default, Karpathy and experimental conditions on a task that reached the
measurement ceiling. The result does not demonstrate an advantage. See the
[trial protocol](agent-trial-protocol.md) and
[recorded report](../artifacts/agent-trials/development-v2-report/README.md).
New model trials are blocked until the runner and confined grader are
integrated and independently qualified; the existing launch refusal must remain
in place until then.

The [2 November upstream observation](../artifacts/research/2026-11-02/karpathy-baseline-head.json)
found that the Karpathy-derived baseline's upstream default-branch head matched
the pinned commit. This time-bound check does not establish quality or cover
other sources.

## Ordered work

1. **Preserve and refresh the inventory.** Keep every skill, source lock,
   resource, category and prior failed result traceable. Compare pinned sources
   with current stable releases or the documented branch policy; review actual
   changes, license scope and missing paths before updating a lock. Regenerate
   mirrors only through the source-lock process and invalidate affected reviews.
2. **Complete bounded research for every skill.** Work category by category,
   recording every bundled resource, applicable official sources, testable
   requirements, dependencies, known limits and review evidence in the ledger.
   Separate source inventory from review and a review from an evaluation. Do
   not mark missing evidence as success; preserve failures and explain when a
   skill is unsuitable or cannot be evaluated.
3. **Qualify improvements.** Preserve immutable source mirrors. Where research
   supports a change, create an attributable maintained or repaired overlay,
   preserve the original and test behavior against independently stated
   contracts. Check installation, runtime, supported hosts and agent entrypoints
   for the specific change. Reassess overlays after relevant upstream updates.
4. **Build representative agent experiments.** Independently define realistic
   task distributions, fixtures, expected outcomes and graders without deriving
   answers from the skill under test. Include full repository workflows,
   category-specific tasks and negative controls; validate graders on known-good
   and known-bad changes. Keep development and untouched holdout tasks separate.
   Complete and qualify the runner and grading boundary before any new trials.
5. **Measure, improve and repeat.** Freeze the task selection, conditions,
   model settings, budgets, stopping rules and analysis plan. Compare default,
   Karpathy and collection conditions using matched tasks and independent
   sessions that comply with repository policy. Record all attempts, failures,
   costs and limitations. Iterate on development results, then evaluate frozen
   candidates on untouched holdouts with uncertainty and multiplicity accounted
   for. Test natural skill selection and individual skills as well as bundles;
   report null or negative results and do not generalize beyond the tested
   tasks and models.
6. **Qualify delivery.** Verify reproducible installation and mandatory tool
   operation on each documented supported host, pinned dependencies and
   workflows, clean generated artifacts, source notices and links. Resolve
   outstanding code-scanning, dependency, DeepSource and security workflow
   findings without suppressing them; document any genuinely unresolvable
   findings with evidence. Security-related implementation is currently
   deferred under the owner's instruction, and readiness cannot be claimed while
   its required checks remain unresolved.
7. **Finish presentation and audit.** Carry out the architecture review and
   tested refactor described below alongside the ongoing qualification work;
   finish the README rewrite after the resulting interfaces are stable, for end
   users and keep contributor material separately linked. Publish reproducible
   graphs only for validated results. Check all release requirements against
   the final commit and completed hosted workflows, including open pull requests
   and alerts. Tell the owner when the evidence supports readiness; do not
   publish a release or create a tag without a later explicit request.

Development stays on `main`. Do not modify the owner's other repositories for
this work. Any previous external reference remains evidence, not permission to
change another repository.

## Architecture reconsideration and refactor

The owner requested a renewed architecture review on 9 November 2026. At commit
`8b5ebf384ce367922a2f557361b4db7c403211bf`, the tracked tree contains 22,002
files: 18,876 under `included/`, 1,756 under `artifacts/`, 824 under `docs/`,
112 under `tools/` and 141 under `tests/`, with 44 workflow files. Of the
documentation files, 689 belong to the generated catalog. These counts describe
the migration scope; they do not establish duplication or justify deleting
provenance. Inventory paths with Git's NUL-delimited output to preserve names.

Implement the refactor in coherent migrations on `main`, with each migration
updating implementation, callers, documentation and verification together:

1. **Map contracts and ownership.** Inventory supported CLI commands, JSON
   schemas, exit codes, installed entrypoints, generated paths and their
   consumers. Identify which files are maintained code, source-locked inputs,
   generated outputs or historical evidence. Record actual duplication and
   dependency relationships before deciding which modules to merge or move.
2. **Consolidate maintained tooling.** Review the responsibilities of the flat
   tooling scripts and shared library directories. Move related implementation
   into descriptively named modules where this reduces coupling or repeated
   behavior. Preserve supported CLI interfaces or provide an explicit migration;
   avoid adding empty indirection. Keep benchmark scoring independent of skill
   generation and source mirroring.
3. **Unify artifact publication contracts.** Evaluate a shared mechanism for
   repair manifests, evidence hashes, provenance and portable line endings.
   Migrate each producer and validator together. Preserve historical bytes,
   source locks and measured results; retaining a digest is not permission to
   rewrite the evidence it identifies. Require deterministic regeneration and
   rejection of stale or missing inputs.
4. **Reconsider workflow structure.** Map each workflow to its actual inputs,
   installation graph, supported runtime and acceptance checks. Consolidate
   repeated setup only when the shared contract is verified. Measure redundant
   work before optimizing triggers or caching, and check that every affected
   consumer still runs. Preserve required gates and failure reporting.
   Security implementation remains outside the active scope while paused.
5. **Simplify navigation and distribution.** Give users a short installation
   and selection path, with scope and evidence limits visible before adoption.
   Link contributor operations separately. Keep generated catalog navigation
   generated, and validate links and packaged resources after moves. Review
   superseded narrative documents for conflicts without deleting unique audit
   evidence or historical failures.
6. **Qualify the migrated repository.** Reproduce the supported installation
   and invocation paths from a clean checkout. Compare generated bytes,
   benchmark outcomes, CLI results and failure behavior with the recorded
   pre-migration contracts. Run the required local gates, then wait for hosted
   checks on the final commit. Report measured runtime or maintenance benefits
   only when comparable evidence exists.

This sequence is an implementation plan, not a completed architecture audit.
It does not replace the outstanding skill reviews, manual review, independent
agent experiments or delivery requirements above. Final structural cleanup
must preserve those obligations and their evidence.

The first tooling migration moves task-declaration validation into
`tools/_trial_declarations.py`, shared by partition preflight and multi-task
reporting. Preflight no longer imports either trial scorer. Existing declaration
tests move with their implementation, and a separate-process regression check
protects that dependency boundary. The checked historical multi-task report and
development partition report remained byte-identical during local comparison.
This migration changes module ownership; it establishes no agent-performance
or execution-speed improvement.

The second migration separates descriptive outcome calculations into
`tools/_trial_summary.py`. Multi-task orchestration retains protocol and
trial-file verification and the CLI. Analysis and chart consumers import the
shared calculations directly, while token-usage validation is shared through
`tools/_trial_comparisons.py`. A process-level check ensures the summary core
does not load either trial verifier. The moved calculation functions retain
their syntax trees, and local historical and partition CLI outputs remain
byte-identical. These are compatibility checks, not efficacy measurements.

## Evidence needed to declare readiness

- All catalog entries and resources have a source-bound research disposition,
  and each applicable skill has independently validated evaluation evidence or
  a clearly justified, evidenced non-applicable disposition.
- Maintained overlays, supported installation paths, required tools and current
  workflows pass their documented checks on the final source revision.
- Preregistered held-out comparisons show a practically meaningful and
  statistically supported advantage over both requested baselines in the
  specified population, with failures and uncertainty retained. A win in one
  task, static coverage or an adapter smoke check is insufficient.
- Required security and dependency findings are resolved or individually
  documented with evidence, without hiding them; final hosted checks and the
  owner’s no-release instruction are respected.

There is no defensible completion date or overall percentage until the
remaining research, qualification and trials reveal their actual scope.

## Execution and decision points

The work above is a dependency plan, not a promise that every skill can be
made useful or that a desired benchmark result can be produced. Continue
independent non-security work while the owner's security-work pause applies.
In particular:

1. Use the ledger to select bounded non-security groups and inventory every
   remaining resource. For each group, record its source revision, applicable
   documentation, reviewed resources, behavior contracts, limitations and
   supporting evidence. Review changes to a source before refreshing its lock;
   re-open stale evidence when its inputs change. The group is complete only
   when every entry has an evidence-backed disposition, not merely an inventory.
2. Implement supported fixes as attributable overlays, or record why an
   upstream-only issue or unsuitable skill remains unresolved. Verify each
   overlay against independent behavior contracts and its installation and
   entrypoint paths. Preserve the upstream mirror and original source text.
3. Prepare a diverse development task set before selecting final holdouts.
   Record each task's real source and revision, issue, license, environment,
   independently specified cases and evaluator controls. Exercise known-good
   and meaningfully different bad variants. Keep these public development tasks
   and any tuning based on them out of the final holdout set. Calibrated cases
   alone do not show that agents find a task difficult or that skills help.
   Record source-group lineage and check overlap between development and
   held-out inputs; exact hashes alone do not rule out reordered, derivative or
   semantically related cases. Declare the scope and limits of those checks.
4. Before model trials, integrate and qualify the runner and grading boundary.
   That qualification is deferred while security-related work is paused; the
   existing refusal to launch new trials remains in force. Once it is permitted
   and complete, freeze task selection, sample sizes, allocation, budgets,
   failure handling, the primary outcome and a practically meaningful effect
   threshold before evaluating. Include source selection and natural skill
   discovery in the design, with separate baseline, Karpathy-derived and
   collection conditions. Retain every outcome and report uncertainty and
   multiple comparisons according to the frozen analysis plan.
5. Use development results to revise supported skills and re-run affected
   controls. Freeze the final candidate and evaluate it on untouched holdouts;
   report results even if the desired improvement is absent. An inconclusive or
   negative result calls for investigation or a narrower claim, not a release
   recommendation or a changed success threshold after observing outcomes.
6. After the substantive work, perform the requested end-user documentation,
   layout and cleanup pass, then validate the exact final revision locally and
   in hosted workflows. Security-related checks and unresolved findings remain
   readiness dependencies even though their implementation is currently
   deferred. Report readiness only after all applicable evidence has been
   reviewed; do not create a release or tag.
