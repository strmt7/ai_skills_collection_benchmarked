---
name: npm-cache-install
description: Configure npm dependency caching in GitHub Actions without skipping the installation needed in a fresh workspace.
license: Apache-2.0
---

# Install npm dependencies after restoring a cache

Apply the repository's [mandatory agent tools](../../../../../../../docs/agent-tools.md)
and its controlling instructions. This repair covers the npm cache behavior
below, not the original action's other package-manager paths.

The source action caches the directory reported by `npm config get cache`,
then skips `npm ci` on an exact cache hit. That directory is a download cache,
not the project's installed `node_modules`. A fresh job can restore that cache
and still have no installed dependencies. Run the appropriate installation
command even when the package cache is restored; the cache can make the install
faster but is not a substitute for it.

For an npm project with a committed lockfile, the [example workflow](examples/npm-ci.yml)
uses `actions/setup-node`'s npm cache and runs `npm ci` unconditionally. It
assumes `package-lock.json`, `package.json`, and the `test` script are at the
repository root. Adapt the Node version and test command to the project. For a
subproject, select its lockfile for the cache key and run `npm ci` from the
same package directory. A missing or inconsistent lockfile must remain an
installation failure, not a reason to skip validation.

Do not generalize this result to every cache layout: an explicitly cached
installed tree has different behavior and needs its own invalidation and
platform-compatibility review. Yarn and pnpm are not qualified by these npm
controls. The [review](../../../../../../../docs/research-npm-cache-install.md)
records tested environments and limitations. Component tests do not establish
an agent-performance advantage.
