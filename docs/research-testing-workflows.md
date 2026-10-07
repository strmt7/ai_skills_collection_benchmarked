# Testing workflow research, first bounded batch

Read the complete entrypoints and `agents/openai.yaml` for ECC's `tdd-workflow`,
`verification-loop`, `bun-runtime` and `e2e-testing`. Each mirrored package has
these two files. Reviewed the complete differences against current ECC v2.2.3,
commit `c05b2d6614f62f6db0047669aa4eefb223d478f9`. This starts four reviews; it
does not complete the 19-skill category or establish coding-agent gains.

## Verification loop

Build, type, lint and test commands pipe to `head` or `tail` without preserving
the producer's exit status. Actual isolated POSIX controls reproduce a command
exiting 7 whose pipeline reports 0. A command printing SUCCESS can still exit 9.
The current upstream body retains these patterns. Preserve the real status and
complete bounded logs before displaying excerpts; never grade log wording.
`benchmarks/dependency-regressions/verification_pipeline.py` is reproducible,
and `verification-pipeline-controls.json` records actual outcomes.

The security phase greps two strings and console logging only in selected JS
extensions, then labels the result PASS/FAIL. It cannot establish dependency,
history, other-language or code-scanning cleanliness. Resolve actual project
gates and report inaccessible/not-run checks distinctly. Diff review should
cover the intended change and existing worktree state, including staged and
untracked files; `HEAD~1` is not always the relevant base. Preserve unrelated
user changes and bind verification to the tested input signatures.

A fixed 80% threshold and repeating all gates every fifteen minutes are not
universal requirements. Keep repository mandates, choose checks by affected
contracts and regressions, and repeat broader checks when changes or unresolved
concerns justify them. Report passed, failed, skipped, aborted and not-run work
separately. Do not suppress findings or manufacture a success verdict.

The explicit MIT-licensed `included/improved/skills/verification-loop-current/`
overlay implements these decisions. Its provenance retains the exact mirrored
entrypoint, and the improved-skills manifest hashes every packaged file. It is
experimental: no independent agent trial yet establishes an individual gain.

## TDD workflow

The original prescribes tests before every change, one assertion per test,
80% coverage, no skips, fixed execution times and E2E tests for all development.
These can create low-value tests and misleading completion signals. Require
tests that detect the intended failure and meaningful wrong outcomes; related
assertions can establish one behavior. Coverage identifies untested execution,
not an independently correct oracle. Explain genuine platform skips without
silently dropping required coverage. Reversible formatting-only changes do not
need tests that restate the edit.

Current upstream adds runner discovery and Bun examples, but invokes an ECC
repository-level detector absent from the standalone package. Its "Bun present"
heuristic can override custom or Node-native tests. Inspect the repository's
actual scripts, lockfiles and runner configuration; a package manager is not a
test runner. Jest/Vitest/Bun APIs and mocks need their own imports and setup.
Retain a real failing-before/passing-after regression where appropriate rather
than counting placeholder test bodies as completed tests.

The fixed 2025 end date, fixed result counts and sleep-based search example need
controlled fixture data and clocks. The coverage-upload action and Node/action
versions in examples are stale. Resolve current stable release identities and
test the workflow inputs instead of copying version strings unchanged.

## Playwright E2E testing

The original fills/clicks before registering response waits, reads counts without
retrying, and repeatedly waits for network idle. Current official
[response-wait examples](https://playwright.dev/docs/api/class-page#page-wait-for-response)
arm the wait before the triggering action. Match request identity and result
status, then verify UI outcomes. Official
[web assertions](https://playwright.dev/docs/test-assertions) retry observable
conditions; immediate scalar assertions can inspect stale state. The
[load-state documentation](https://playwright.dev/docs/api/class-page#page-wait-for-load-state)
discourages using network idle as test readiness.

Actual headless Chromium/localhost controls with Playwright 1.63.0 reproduce a
late subscription after known response completion, a stale immediate count, and
network-idle timeout while UI assertions pass. Prearmed query-specific waits and
retrying assertions pass. All external requests are blocked. This demonstrates
valid failure schedules; it does not claim every fill-then-wait always fails.
The public `playwright_wait_controls.mjs` and `playwright-wait-runtime-controls.json`
retain scope, versions, source hash and complete control results.

The mirrored `videosPath` Playwright Test option and `snapshots` Chromium tracing
option are rejected by current package types. A corrected fixture using
`outputDir`, `video`, `trace` and current locator/response APIs compiles under
TypeScript 7.0.2 and Node types 26.6.4. The first compiler invocation failed to
resolve staged Node types; those harness logs remain, and the corrected cwd run
separately establishes the two real API errors and passing positive fixture.
`playwright-current-contract-review.json` records both classifications.

Tracing APIs for Chromium profiling and Playwright context/test traces are
different. Configure artifacts through the chosen supported API and close
contexts so videos finish. Control fixtures, seeds and auth state; traces and
screenshots can contain sensitive data. Retain retry/flaky outcomes. Quarantine
needs an explicit remaining-coverage record, not a claim that skipped work passed.
Production guards based only on NODE_ENV are insufficient when BASE_URL is
independent; use explicit permitted test targets and mock/sandbox mutations.
No real trade, live service or owner repository was modified by these probes.

## Bun runtime

The package concerns runtime/package-manager selection more broadly than tests;
review semantic category routing during the final refactor. Its drop-in and
speed claims need project-specific evidence. The official
[compatibility matrix](https://bun.sh/docs/runtime/nodejs-compat) still describes
partial and missing Node APIs. Verify required modules, native addons, scripts,
installation behavior, framework support and deployment environment before a
migration. Do not replace a working toolchain solely because Bun is available.

Primary release metadata resolves Bun `1.4.2` and Playwright Test `1.63.0` in
`testing-stable-version-review.json`. Package installation, lockfile behavior,
script trust, Node compatibility and cold/warm workload performance remain
separate qualifications. Distinguish Bun's package manager from `bun:test`,
and preserve the declared project's runner and reproducible dependency graph.

The isolated Playwright/TypeScript dependency graph passes npm advisory auditing
with zero known findings; its metadata includes optional platform dependencies.
The bundled headless browser is the Playwright-selected revision, not a claim
about the newest standalone Chrome stable release or browser security absence.
No Bun runtime or Vercel deployment has yet been exercised.

Remaining: other explicit revisions, independent agent comparisons, full runner/framework
fixtures, current Bun runtime qualification, artifact/privacy controls and the
other fifteen testing skills. Immutable mirrors remain unchanged.
