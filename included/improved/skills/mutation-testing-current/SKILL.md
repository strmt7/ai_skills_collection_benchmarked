---
name: mutation-testing-current
description: Configure or review mutation testing for an existing test suite. Use when asked to scope a mutation campaign, check test assertions against changed behavior, investigate surviving mutants, or report a mutation score.
license: CC-BY-SA-4.0
compatibility: StrykerJS 10.1.1 is qualified for a scoped Node.js command-runner campaign on Windows x64. Check the release and platform for other providers and runners.
metadata:
  source: trailofbits/skills
  revision-status: experimental-unbenchmarked
---

# Mutation testing that measures test behavior

1. Identify the behavior the suite is meant to enforce. Record the source
   revision, test runner, focused target files, and requested environment.
   Exclude tests, generated code, and third-party files from mutation targets.
   Run the unchanged reference and retain its exit status and output.
2. Select a tool for the language, runner, and platform. Pin the exact
   version through the project's documented dependency setup. Inspect the
   effective configuration and actual target inventory. See
   [provider checks](references/providers.md) for Mewt, Muton, and StrykerJS.
3. Use a disposable copy with bounded time, output, storage, and processes.
   Keep the original source and prior results recoverable. Measure a small
   representative sample, including recompilation and setup costs, before
   estimating the whole campaign. Retain the measured range and its limits.
4. Verify that an assertion catches an independently specified wrong outcome.
   A deliberately weakened test or a known uncovered branch can verify the
   tool produces a survivor. A failing unchanged suite invalidates the
   campaign. Preserve timeouts, test-runner errors, and incomplete attempts.
5. Classify survivors against the actual behavior or contract. A change can
   be equivalent within the supported domain, unreachable, uncovered, or
   accepted by an assertion. Reproduce any test improvement with both the
   unchanged reference and the changed behavior. Preserve unresolved cases.
6. Save the effective configuration, native results, attempted scope, wall
   time, and source identities. Check original bytes after the campaign and
   confirm the tool and runner stopped. Preserve the result before purging
   its database or expanding scope.

Report the tool's score and its documented denominator alongside raw counts.
Distinguish detected, survived, equivalent where justified, timed out,
invalid, skipped, and unexecuted outcomes. Compare results only when the
source, operator set, filters, and denominator are comparable. If a targeted
phase precedes a broader suite, preserve the first phase and predeclare how
the second will handle skipped, timed-out, and other unresolved changes.

Summarize the behavior the tests now distinguish, the observed limitations,
and the smallest useful next check.