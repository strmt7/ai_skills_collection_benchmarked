---
name: eval-harness-evidence
description: Design and verify matched coding-agent evaluations when comparing skills, prompts, models, or harnesses using executable acceptance checks and native result evidence.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: 846ffb75da9a5f4e677d927af1ad4a1951652267
  revision-status: experimental-unbenchmarked
---

# Controlled agent evaluation

Define the decision, comparison, target task population, primary metric, and
smallest useful effect before looking at confirmatory results. Keep the task
inputs and acceptance checks independent of the instructions under evaluation.

1. **Choose tasks and conditions.** Pin real issues, workflows, or independently
   specified requirements. Include meaningful regressions and cases beyond the
   failure that motivated the change. Freeze the candidate and reserve tasks
   that were never used to select or revise it. In a matched block, use the same
   task, model, reasoning effort, ordinary tools, dependencies, and budgets.
   Change only the declared intervention. Use fresh subject state and balance
   condition order. Record the requested and observed model identities separately.
2. **Qualify the evaluator.** Check a known valid result, a plausible wrong result,
   and an incomplete run. For a repair task, reproduce the original defect and
   keep unrelated valid behavior passing. Keep expected answers outside the
   subject workspace. Score observable behavior. Use blinded judgment only
   for criteria that executable checks cannot settle.
3. **Admit each result.** Keep the declared task and scorer revisions, actual
   submission, native reports, exit or completion signal, scope checks, and
   resource observations together. Check that the scorer graded the submitted
   bytes. Reconcile the expected case IDs and counts with the reported outcomes
   before accepting a score. A script can exit zero after an internal test
   failure. A reporter can merge cases and use a different denominator from
   the underlying test runner. Preserve the official metric and its unit.
   Label other counts as diagnostics.
4. **Account for every attempt.** Distinguish a complete task failure from an
   interrupted run, unavailable grader, or invalid scope. Keep unscored
   attempts visible and leave unavailable usage or timing unknown. Compare
   paired task outcomes and report uncertainty, coverage, and exclusions.
   Treat repeated samples on one task as repeated observations of that task.
   Use [repeated-attempt metrics](references/repeated-attempts.md) for best-of-k,
   all-of-k, and incomplete outcomes.
5. **Iterate on development evidence.** Fix a general failure mechanism, rerun
   affected checks, and compare with the frozen baselines on untouched tasks.
   Compare resource use for comparable outcomes. Report neutral, harmful, and
   inconclusive effects alongside improvements.

Package checks, oracle controls, and native runner qualification measure their
own scopes. A skill-effect claim requires measured outcomes from the declared
agent comparisons.
