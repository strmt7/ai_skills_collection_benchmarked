# pnpm package store and installation review

The pinned GitHub Actions generator caches `pnpm store path` but skips its
install step on an exact cache hit. Its default lockfile pattern targets npm's
`package-lock.json`. A pnpm store contains package data, not a fresh project's
installed dependency tree. The maintained [pnpm repair](../included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/pnpm-cache-install/SKILL.md)
provides a GitHub Actions example using the official pnpm setup action, store
caching, and a required frozen-lockfile installation.

The [pnpm install reference](https://pnpm.io/cli/install) describes offline and
frozen-lockfile modes. The [CI documentation](https://pnpm.io/continuous-integration#github-actions)
recommends `pnpm/setup`, and its `require-lockfile` input requires a lockfile
and runs a frozen install. pnpm 12 is a native executable; a project's selected
version and runtime must still be provisioned and compatible. The example is
for a root project; adapt it for the actual repository and workspace.

The [independent offline control](../artifacts/repaired-skill-readiness/pnpm-cache-install-v1/reproduce.py)
uses a local tarball dependency, a newly generated lockfile, and an isolated
store. A fresh project cannot load the dependency before installation; an
offline frozen install makes it loadable. The control rejects an absent or out-of-date
lockfile and a missing local tarball, even after store restoration. Local results
cover [Windows, Node 26](../artifacts/repaired-skill-readiness/pnpm-cache-install-v1/windows-node26-pnpm12.json)
and [Linux, Node 24](../artifacts/repaired-skill-readiness/pnpm-cache-install-v1/linux-node24-pnpm12.json),
both with pnpm 12.16.1. A [hosted workflow](../.github/workflows/pnpm-cache-install.yml)
repeats the control and compares a simulated source cache-hit decision with the
maintained action using real GitHub cache hits. It does not execute the original
composite action in the pnpm comparison.

These controls cover a synthetic fixture and do not establish broad workspace
compatibility, complete offline build inputs, or an agent-performance advantage.
The original mirror remains unchanged.
