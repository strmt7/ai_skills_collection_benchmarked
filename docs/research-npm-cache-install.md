# npm cache and installation review

The pinned GitHub Actions generator includes a composite action that caches the
directory reported by `npm config get cache` and skips `npm ci` on an exact cache
hit. That cache contains package data; it is not the project's installed
`node_modules`. The current [setup-node documentation](https://github.com/actions/setup-node/blob/main/README.md#caching-global-packages-data)
likewise distinguishes its package cache from `node_modules` and runs `npm ci`
after cache restoration.

The [npm-cache-install repair](../included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/npm-cache-install/SKILL.md)
provides a workflow that restores the npm package cache and still installs from
the lockfile. It covers npm only; the source action's Yarn and pnpm paths and
other generator features remain unqualified. The original entrypoint and action
are retained in the repair's provenance directory and the catalog mirror is unchanged.

For the hosted source-action check, upstream release `v1.0.0` resolves to the
same pinned source commit, `7fe7595e4512f8ce43dcf956aa5190b96d627dd1`.
On 2 November 2026 the upstream action file's Git blob
`3af2916939f377f36dc35fee8cccb4f3ace61deb` matched the catalog mirror byte for
byte. The hosted workflow uses that immutable upstream reference so the normal
stable-release audit can review it; the local control checks the mirrored bytes.

## Component evidence

The [independent control](../artifacts/repaired-skill-readiness/npm-cache-install-v1/reproduce.py)
creates a local package and lockfile, populates a dedicated npm cache, copies
only the manifest and lockfile into a clean workspace, and restores the cache.
With no `node_modules` or local package archive, the simulated source cache-hit
path cannot load the dependency. Running `npm ci` offline installs it from the
restored cache, after which it loads successfully. Separate cases confirm that
missing and mismatched lockfiles fail. All test packages and npm configuration
are isolated; the control does not use a package registry.

On 2 November 2026 the control passed on Windows with Node 26.13.0 and both npm
12.2.1 and its bundled npm 11.20.0, and on Linux with Node 24.15.0/npm 11.12.1. The
[qualification](../artifacts/repaired-skill-readiness/npm-cache-install-v1/qualification.json)
binds the source, repair, runner and recorded observations. The
[hosted workflow](../.github/workflows/npm-cache-install.yml) also runs the
offline control on Windows and Linux and is designed to exercise actual GitHub
cache hits on fresh Linux jobs. Its run artifacts contain native stdout and
stderr. These controls do not establish broad generator compatibility or an
agent-performance advantage.
