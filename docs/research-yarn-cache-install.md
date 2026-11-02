# Yarn 4 package cache and installation review

The pinned GitHub Actions generator invokes `yarn cache dir` and skips its
install step on a cache hit. Its default lockfile pattern targets npm's
`package-lock.json`. Yarn 4.18.1 rejects that cache command; Yarn Classic 1.22.22
accepts it in a separate local command check. The source action itself was not
run in these Yarn component controls.

The [Yarn 4 repair](../included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/yarn-cache-install/SKILL.md)
recommends provisioning the project-selected package manager, choosing the Yarn
lockfile for a cache key, and performing `yarn install --immutable` after cache
restoration. Yarn's [configuration reference](https://yarnpkg.com/configuration/yarnrc)
describes `cacheFolder` and `enableGlobalCache`, and its [install reference](https://yarnpkg.com/cli/install)
describes linking and immutable installs. [Node's Corepack documentation](https://nodejs.org/download/release/v25.8.0/docs/api/corepack.html)
states that Corepack stopped being distributed with Node beginning with Node 25;
individual machines may have it separately installed.

The [reproducible control](../artifacts/repaired-skill-readiness/yarn-cache-install-v1/reproduce.py)
creates a local tarball dependency and lockfile, restores only package-cache
archives into a fresh fixture with the source tarball present, and exercises
both `node_modules` and Plug'n'Play linking with networking disabled. Both
fail to load the dependency before installation, succeed after an immutable
install, and reject a mismatched lockfile. It checks the source command, Yarn's
reported cache directory, and the locked source-action hash. The recorded
[Windows result](../artifacts/repaired-skill-readiness/yarn-cache-install-v1/windows-node26-yarn4.json)
uses Node 26.13.0 and Yarn 4.18.1. A [Linux result](../artifacts/repaired-skill-readiness/yarn-cache-install-v1/linux-node24-yarn4.json)
uses Node 24.15.0 with the same Yarn version. Native command streams are
retained by the control; CI uploads them separately.

This local fixture does not show that the cache alone can replace the source
tarball, exercise the GitHub cache service or the complete original composite
action, cover all Yarn configuration modes, or establish an agent-performance
advantage. The immutable source mirror remains unchanged.
