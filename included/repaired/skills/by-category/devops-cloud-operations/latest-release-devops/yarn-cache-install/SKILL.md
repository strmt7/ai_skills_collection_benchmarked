---
name: yarn-cache-install
description: Install a locked Yarn 4 project after restoring its package cache in a fresh job.
license: Apache-2.0
---

# Install Yarn 4 dependencies after restoring the package cache

Apply the repository's [mandatory agent tools](../../../../../../../docs/agent-tools.md)
and controlling instructions. This repair addresses Yarn 4 only.

The source action calls `yarn cache dir`, a Yarn Classic command rejected by
Yarn 4. For Yarn 4, `yarn config get cacheFolder` reports the configured cache
location. Select `yarn.lock` as the lockfile input to cache-key mechanisms,
and follow the project's Yarn configuration. The source action defaults to a
`package-lock.json` pattern, which is not a Yarn lockfile.

Ensure the project's declared, compatible Yarn version is available in the job
before invoking it. Do not assume Corepack ships with every Node installation:
Node stopped distributing it starting with Node 25. Provision the project's
chosen package manager using its documented installation mechanism.

Run `yarn install --immutable` in the project directory even on a package-cache
hit. Cached package archives are not the linked project state. This matters for
both `node_modules` and Plug'n'Play projects. Keep an inconsistent lockfile as
an installation failure. Respect project-specific zero-install and cache
configuration; verify those arrangements before making broader assumptions.

The [component review](../../../../../../../docs/research-yarn-cache-install.md)
records the exact offline fixture and its limitations. It does not qualify Yarn
Classic, pnpm, a real GitHub cache service, or agent performance.
