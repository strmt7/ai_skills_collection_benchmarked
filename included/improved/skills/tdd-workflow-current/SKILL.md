---
name: tdd-workflow-current
description: Use when changing software behavior, repairing a regression, or adding tests. Verify that focused tests distinguish correct behavior from the relevant defect.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  revision-status: experimental-unbenchmarked
---

# Test-driven development

Read the repository instructions and `docs/agent-tools.md`. Apply Caveman for
every task, CocoIndex Code before broad navigation, and Crawl4AI for web
research. Keep the required execution evidence.

## Define the contract and reproduce

- Identify the behavior a caller can observe, the affected inputs and failure
  boundaries, and the project's supported runtimes. For ports or compatibility
  changes, derive expectations from the reference contract and compare the
  same inputs against the reference implementation when practical.
- Find the project's declared test commands and dependencies. Use its documented
  setup with compatible versions and keep new caches and environments outside
  deliverables. Choose the smallest relevant unit, integration, browser,
  compiler, or documentation and configuration check. Preserve required gates.
- Before changing production behavior, run a focused test or a concrete
  reproducer. Confirm the intended case executed and failed on the expected
  behavior. For a type contract, require the expected compiler diagnostic at
  the intended call. Collection, setup, teardown, missing dependencies, skipped
  or expected failures, and unrelated diagnostics require separate reporting.
  Record any reason the baseline could not run.

## Implement and verify

- Fix the behavior with the smallest maintainable implementation. Run the same
  case with the same input, assertion, configuration, and command. Confirm it
  executes and passes. Expand to affected consumers, regressions, and required
  gates. If a test needed correction, establish a new baseline when practical.
- Use deterministic data and test the important real integration boundaries.
  Use mocks where isolation is useful and report which boundaries were exercised.
  Register cleanup as each resource is acquired, including during partial setup.
  For asynchronous work, wait for an observable milestone, enforce deadlines,
  and release and join test-owned workers even when an assertion fails. For
  browser checks, use supported selectors and wait for observable conditions.
- Preserve behavioral checks during refactoring. For documentation or
  configuration changes, verify the affected example, parser, or consuming
  command. Prefer tests that distinguish credible regressions from correct
  behavior over assertions that repeat implementation details.

## Add tests to unchanged behavior

Derive expected outputs, order, counts or effects from the caller's contract.
Run the new tests on the unchanged program. When assertion strength matters,
exercise a plausible wrong result in a disposable fixture or with the existing
mutation runner. Confirm that the intended assertion fails. Record collection
errors and cases that never ran separately. Preserve the production program
and choose a few faults that represent the contract under test.

Follow the project's coverage policy. Use coverage to locate unexercised
behavior and check assertions separately. Report commands and observed pass,
failure, skip, setup, and cleanup outcomes with their relevant limitations.
