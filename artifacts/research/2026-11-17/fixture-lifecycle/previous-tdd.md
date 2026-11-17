---
name: tdd-workflow-current
description: Develop or repair software using risk-based behavioral tests, a meaningful failing baseline, and verified regression checks.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: 846ffb75da9a5f4e677d927af1ad4a1951652267
  revision-status: experimental-unbenchmarked
---

# Test-driven development

Read the repository instructions and `docs/agent-tools.md`: apply Caveman for
every task, CocoIndex Code before broad repository navigation, and Crawl4AI for
web-page research; retain the required execution evidence. Identify the
requested behavior, existing contracts and affected environments. Discover the
actual test runner and project commands instead of assuming a package manager
or framework. Choose unit, integration and end-to-end checks according to the
change, existing requirements and risk; preserve required checks.

## Establish a meaningful baseline

For a behavior change or bug fix, define observable outcomes and realistic
boundary and failure cases. Where practical, add a focused test or reproduce the
bug before changing production behavior. Confirm the intended test was collected
and executed, and inspect its failure: the failure should demonstrate the missing
behavior. A nonzero exit from setup, collection, an unavailable dependency or an
unrelated assertion is not that evidence. A skip or expected failure is not an
observed failing assertion. If a baseline cannot be run, record why rather than
claiming it was reproduced.

## Implement and verify

Make the smallest maintainable change that satisfies the contract. Rerun the
focused test and check that it actually executes and passes, then run relevant
regressions and all required project gates. Keep test data deterministic and
isolate and clean up resources owned by the test. Test important integration
boundaries with appropriate real components; use mocks where isolation helps
without claiming that a mocked boundary was exercised end to end.

For browser checks, control the data and wait for observable conditions, not
fixed delays. Use fixtures and selectors supported by the application. During
refactoring, keep behavior-focused checks in place and repeat them after changes.
Do not add tests that merely duplicate implementation details or add no useful
signal for a reversible, low-impact change.

Follow the project's coverage policy and use coverage to identify unexercised
behavior. A percentage alone cannot establish that assertions are correct; do
not invent a universal threshold or weaken an existing gate. Report executed,
passed, failed, skipped and unavailable checks separately, with relevant command
status and limitations. Passing tests reduce uncertainty; they do not prove the
absence of defects.
