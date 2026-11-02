---
name: pnpm-cache-install
description: Install a locked pnpm project after restoring its package store in GitHub Actions.
license: Apache-2.0
---

# Install pnpm dependencies after restoring the store

Apply the repository's [mandatory agent tools](../../../../../../../docs/agent-tools.md)
and controlling instructions. This repair addresses pnpm 12 store caching.

The source action caches `pnpm store path` but skips installation on an exact
cache hit. A restored store supplies package data; it does not install or link
`node_modules` in a fresh checkout. Its default cache-key pattern also selects
`package-lock.json`, not `pnpm-lock.yaml`.

Ensure the project's selected pnpm version and runtime are available. For a
GitHub Actions project with a committed lockfile, the [example](examples/pnpm-ci.yml)
uses pnpm's official setup action to restore the store and require a frozen
installation in every job. Adapt the runtime, package-manager version, working
directory, and test command to the project. For a workspace, use its actual
shared lockfile and package configuration. Never skip installation merely
because the store cache was restored.

A local tarball or other project input may still be needed even when package
content is cached. Validate project-specific offline and cache behavior rather
than assuming a store is a complete build environment. The [component review](../../../../../../../docs/research-pnpm-cache-install.md)
records tested configurations and limitations; it does not establish an
agent-performance advantage or qualify other package managers.
