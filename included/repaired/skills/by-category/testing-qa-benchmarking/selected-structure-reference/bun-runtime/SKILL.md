---
name: bun-runtime
description: Evaluate, run, or migrate Bun projects with explicit runtime, dependency, and deployment compatibility checks.
---

# Bun runtime and package manager

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Inspect the project's existing runtime requirements, package manager, lockfile, scripts, deployment target, and tests before choosing Bun or changing a Node project. Keep the current toolchain unless the requested change justifies migration. Check compatibility for the actual dependencies and APIs and run the project's relevant tests under the intended runtime. Bun implements many Node APIs but is not behaviorally identical; do not infer compatibility or speed for a particular application without measurement.

Use the project's documented, supported Bun version and package scripts. Run a focused check first, then the relevant build, tests, integration checks, and deployment qualification. Measure performance with representative workloads and controlled conditions when performance is the reason for a change. Report versions, commands, results, and limitations.

For a locked install, first verify that the intended project lockfile exists, is the one the deployment consumes, and corresponds to the manifest and workspace. Then use the project's documented frozen-install command, such as `bun install --frozen-lockfile`. Bun 1.4.4 can succeed without creating a lockfile when none exists, so the flag alone is not evidence of a locked install. Bun can also migrate supported non-Bun lockfiles in memory; check the current documentation and preserve existing project files during any migration. Do not generate or replace a lockfile without the requested scope and verification.

Vercel's Bun runtime is documented as beta. When targeting it, check the current Vercel documentation, supported framework, runtime constraints, and accepted `bunVersion` values in `vercel.json`; qualify the exact application before deployment. Do not assume that selecting a package manager also selects the function runtime, or that a local run proves deployment compatibility.

The original upstream skill is preserved at `provenance/original.SKILL.md`. This maintained overlay corrects selected compatibility, lockfile, and deployment guidance. Component controls do not measure agent effectiveness.
