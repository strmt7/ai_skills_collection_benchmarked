---
name: tdd-workflow
description: Plan, run, and report risk-based tests for software changes, using project-specific test and coverage requirements.
---

# Test-driven development workflow

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Start with the requested behavior, the existing project instructions, and the affected contracts. Identify meaningful failures and choose unit, integration, or end-to-end tests appropriate to the change. Reproduce a bug or make a focused test fail before the repair when practical. Implement the smallest maintainable change, run the focused checks, and broaden them when project rules, risk, or observed failures require it. Avoid tests that merely restate an implementation or padding a metric.

Discover the actual commands and test runner from the project configuration. Use deterministic fixtures and clean up test-owned resources. Prefer observable behavior and important error paths over private implementation details. Mocks can isolate a unit, but validate integration boundaries with suitable real components when those boundaries matter.

For browser tests, set up controlled data, register any response wait before the action that triggers it, and use retrying assertions against observable results. Do not use a fixed sleep as a readiness signal. Use only routes, selectors, counts, clocks, and environment assumptions supplied by the application and its fixtures.

Coverage reports help locate unexercised code; they do not establish that assertions or behavior are correct. Honor the repository's existing coverage policy and report the measured scope, missing coverage, and genuinely unavailable checks. Do not invent a universal threshold or weaken an existing requirement. For a project that explicitly requires an 80% Jest threshold, its `package.json` configuration uses the singular option:

```json
{
  "jest": {
    "coverageThreshold": {
      "global": {
        "branches": 80,
        "functions": 80,
        "lines": 80,
        "statements": 80
      }
    }
  }
}
```

Run Jest with coverage enabled when enforcing that configuration. Use the project's installed runner and version; verify its exit status and output. Report what passed, failed, was skipped, or was not run, and avoid claiming testing proves the absence of defects.

The original upstream skill is preserved at `provenance/original.SKILL.md`. This maintained overlay corrects selected testing guidance and a Jest configuration example; its component controls do not establish an improvement in agent performance.
