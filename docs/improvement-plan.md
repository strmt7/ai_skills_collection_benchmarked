# Release readiness and work plan

This collection is experimental. It is not ready for a commercial release:
most skills have not completed evaluation, and measured improvement over the
default agent or the Karpathy baseline has not been established. A release or
tag will be created only if the owner later requests one.

## Current state

On 2 November 2026 the [improvement ledger](../data/improvement_ledger.json)
recorded 673 skills: research was complete for one, in progress for 317 and
pending for 355; evaluation was in progress for 12 and pending for 661. These
are tracking states, not a percentage of release readiness. For current counts,
run `python tools/manage_improvement_ledger.py --check --json`.
The scientific category now has 148 skill-level resource inventories, with
1,268 resource records pending review and three marked reviewed. File records
are scoped to each skill and may overlap between nested packages. Transient
`.git` and `__pycache__` directories follow the catalog hash boundary and are
not source resources. Inventorying a file does not review or evaluate it.

To add pending resource records for another category, first validate the ledger
and mirrors, then run `python tools/manage_improvement_ledger.py
--inventory-category "<exact category name>"`. Existing inventories and review
states are preserved; source changes invalidate associated work through the
ledger's synchronization rules.

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
7. **Finish presentation and audit.** After the preceding work, refactor files
   and folders with tested migrations and links; rewrite the README for end
   users and keep contributor material separately linked. Publish reproducible
   graphs only for validated results. Check all release requirements against
   the final commit and completed hosted workflows, including open pull requests
   and alerts. Tell the owner when the evidence supports readiness; do not
   publish a release or create a tag without a later explicit request.

Development stays on `main`. Do not modify the owner's other repositories for
this work. Any previous external reference remains evidence, not permission to
change another repository.

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
