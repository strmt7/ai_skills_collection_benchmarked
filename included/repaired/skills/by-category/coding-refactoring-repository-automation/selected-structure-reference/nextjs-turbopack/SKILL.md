---
name: nextjs-turbopack
description: Inspect and validate Next.js bundler choices, caching, and bundle analysis for the project's installed version.
---

# Next.js and Turbopack

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Inspect the project's installed Next.js version, lockfile, scripts, configuration, router, and existing tests before changing its bundler or cache settings. Use the installed CLI's help and the official documentation for that version. Preserve project-specific webpack plugins, deployment requirements, and router choices unless the requested task and validation justify changing them.

In Next.js 16.4.3, the documentation describes Turbopack as the default for `next dev` and `next build`; a component control confirmed the build default. The CLI accepts `--webpack` for either command and rejects `--no-turbopack`. These are version-specific observations, not promises for other releases. Turbopack does not implement webpack plugins, so verify plugin and loader compatibility before switching a real project.

For bundle analysis, follow the installed version's official instructions. In the tested release, `next analyze --output` writes analysis files without starting the analyzer server and does not itself produce an application build. Webpack analysis uses a different integration. Treat generated reports as diagnostic evidence, then verify proposed changes with the project's functional and build checks.

When investigating performance, define the workload and success metric, distinguish cold and warm caches, record versions and environment, and use repeated comparable runs. Do not assume a fixed startup, rebuild, or bundle-size improvement. Check the current documentation for filesystem-cache defaults and the actual build environment before changing caching.

Report the commands, versions, bundler, results, and untested environments. The original upstream skill is retained at `provenance/original.SKILL.md`. These component checks do not establish an agent-performance advantage.
