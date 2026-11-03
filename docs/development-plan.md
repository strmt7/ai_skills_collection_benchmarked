# Development plan and release criteria

This plan organizes the remaining work. It is not a release announcement or a
claim that the collection improves an agent. The owner has paused
security-related work and has not authorized a release. Continue independent
non-security work; retain the deferred items as release prerequisites.

## 1. Establish and maintain the inventory

- Validate the [improvement ledger](../data/improvement_ledger.json) and use its
  separate research, revision and evaluation states to select and track work for
  every catalog entry. A shared category review must identify its exact scope;
  it does not automatically complete the review of every skill in that category.
- Review the supplied implementation manual and embedded materials in full,
  recording page and attachment coverage in the existing
  [review ledger](../artifacts/research/2026-11-03/implementation-manual-review/ledger.json).
  Verify applicable claims independently and record decisions, including
  conflicts with the owner's instructions and items outside this repository.
- Check pinned source revisions and applicable upstream changes, provenance and
  licenses. Review changes before updating source locks, regenerate the catalog
  deterministically, and preserve the prior source and evaluation evidence.

Exit criterion: every catalog entry and manual item has a traceable, accurate
disposition supported by evidence, including explicitly deferred work. A count
of in-progress records is not a completed review.

## 2. Research and improve skills

- Work category by category, verify current primary sources and executable
  behavior where applicable, and record applicability, limitations and results.
- Keep source mirrors immutable. Use the documented repair or improved-overlay
  loop for supported changes, with source attribution, regression controls and
  deterministic manifests. Preserve frozen instructions used by prior trials.
- Test installation and behavior on the environments the affected skill claims
  to support. A successful format check or component smoke test is not an agent
  effectiveness result. Mark unsupported, incomplete and untested cases honestly.
- Maintain the mandatory agent tools and their source-bound execution evidence,
  without claiming that an instruction file can enforce another agent's behavior.

Exit criterion: the ledger accounts for each skill's applicable research and
revision, and each supported improvement has reproducible evidence and clear
limitations. Evaluation remains a separate requirement.

## 3. Build and qualify independent benchmarks

- Develop realistic, diverse tasks from independently defined requirements,
  with reproducible fixtures, objective graders and positive and negative
  controls. Cover relevant repository workflows and skills, including failures
  and cases that distinguish alternatives. Keep development tasks separate from
  held-out tasks and never derive expected answers from the skill under test.
- Qualify task isolation, grading, scoring, missing-result handling, provenance
  and replay before interpreting runs. Compare the default agent, the pinned
  Karpathy-adapted baseline and the improved instructions under matched,
  randomized or balanced conditions. Record model identity as far as the
  provider exposes it, budgets, attempts, failures, usage and selection costs.
- Preregister the primary outcome, meaningful effect size, analysis and sample
  plan before held-out evaluation. Report uncertainty and per-task outcomes;
  include regressions and unsuccessful attempts. Avoid pooling attempts in ways
  that change the question being measured. Report cost and time separately from
  quality, with their measurement limitations.
- Iterate using development results, then freeze candidate instructions,
  tasks and evaluators before the held-out comparison. Publish validated raw
  evidence and reproducible summaries and graphs. Adapter smoke tests, scenario
  templates and source-provenance checks do not establish model performance.

The current [development protocol](../benchmarks/agent-effectiveness/development/protocol-v2.json)
has one task and a documented ceiling effect. Its
[nine attempts](../artifacts/agent-trials/development-v2-report/summary.json)
do not establish superiority. Execution of further model trials is contingent on
the separately deferred runner and grader qualification where applicable.

Exit criterion: a predeclared, independently scored held-out comparison supports
a practically meaningful improvement over both baselines, within stated
uncertainty and with no concealed failures. Otherwise report the measured result
and continue development; do not declare success from a tie or a smoke test.

## 4. Product and operational qualification

- Test supported installations, catalog generation, navigation, the mandatory
  development tools and affected workflows on their declared host environments.
  Keep version updates evidence-based and test the resulting configuration.
- Verify all relevant local checks and the completed hosted workflows on the
  exact candidate commit. Investigate failures according to their scope; do not
  suppress findings or treat an unrun check as a pass.
- Finish the deferred security-related audits and remediation only when the
  owner resumes that work. They remain release prerequisites, along with any
  other unresolved defects or missing evidence.
- Once the earlier loops are complete, remove obsolete material carefully,
  preserve provenance, refactor the final structure, and rewrite the README for
  end users with developer material linked separately. Revalidate generated
  artifacts and documentation links after the final changes.

Exit criterion: the exact candidate has passed its applicable checks, all
release prerequisites are resolved with evidence, documentation describes only
verified capabilities, and no required work remains. Notify the owner that it is
ready; do not create a release or tag without a later explicit request.

## Rechecking progress

Use `python tools/manage_improvement_ledger.py --check --json` for current
catalog state, inspect the manual review ledger for coverage, and validate the
trial report against its frozen protocol. Check hosted workflow results for the
exact commit under consideration. These records answer different questions and
must not be combined into a single percentage of completion.
