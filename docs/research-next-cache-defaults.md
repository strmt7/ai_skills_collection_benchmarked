# Next.js filesystem-cache defaults

The experimental [Next.js overlay](../included/improved/skills/nextjs-turbopack-cache/SKILL.md)
distinguishes development and build caching by release. The checks below inspect
selected package configuration exports; they do not run a Next.js server or
build, measure cache persistence or speed, or establish a coding-agent gain.

## Source review

The catalog mirror is pinned to ECC commit
`846ffb75da9a5f4e677d927af1ad4a1951652267`. On 3 November 2026, GitHub reported
`v2.2.3` as its latest stable release; the annotated tag resolves to
`c05b2d6614f62f6db0047669aa4eefb223d478f9`. Its
[skill entrypoint](https://github.com/affaan-m/everything-claude-code/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/nextjs-turbopack/SKILL.md)
has Git blob `b29570308123e721c1aafd657839f2800510b020` and SHA-256
`2beabec4326fc32e652db21378bae5f704c931a6ff50d0496b9c9f1c8340f82d`.
Its body matches the locked mirror after newline normalization; the release
changes `origin` to a licence field in frontmatter. The release's
`agents/openai.yaml` changes the short description and prompt while retaining
implicit invocation. Both files in the locked skill package were reviewed;
the [source observation](../artifacts/research/2026-11-03/next-cache-defaults-v1/upstream-observation.json)
records their identities. This does not qualify every claim or execution
environment.

The upstream entrypoint describes filesystem caching without distinguishing
the initial 16.0 release from later defaults. The current
[Next.js cache documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/turbopackFileSystemCache)
records separate 16.0 opt-in flags, development caching enabled by default in
16.1, and build caching enabled by default in 16.3. It also notes that build
cache reuse requires the build environment to preserve the cache directory.
Explicit project configuration and future releases can differ.

## Package-export controls

On 3 November 2026, the npm registry reported 16.4.4 as the latest stable
`next` package. The [control](../benchmarks/dependency-regressions/next_turbopack_cache.py)
verified the registry SHA-512 identities of four exact package archives, loaded
their exported default configuration in isolated Node processes, and rejected
any loaded package module outside the fixture. It examined a small subset of
each package, not a complete installed application.

| Package | Development field | Build field |
| --- | --- | --- |
| 16.0.0 | Absent | Absent |
| 16.1.0 | `true` | `false` |
| 16.3.0 | `true` | `true` |
| 16.4.4 | `true` | `true` |

An absent field is an observation about `defaultConfig`; it is not itself a
runtime measurement of the cache. The published 16.0.0 Turbopack utility
falls back to false for the missing flags, consistent with the documentation's
opt-in description. The controls ran serially on Windows with Node 24.22.2 and
Linux with Node 24.15.0. [Windows](../artifacts/research/2026-11-03/next-cache-defaults-v1/windows-result.json)
and [Linux](../artifacts/research/2026-11-03/next-cache-defaults-v1/linux-result.json)
records include archive identities, source hashes, runtime hashes and the modules
actually loaded. A modified recorded boolean and an invalid archive were rejected.

To reproduce, obtain the four exact `next-<version>.tgz` archives from the npm
registry into a directory outside the repository, then run:

```sh
python benchmarks/dependency-regressions/next_turbopack_cache.py --archives /path/to/archives --output /path/to/new-result.json
```

The control verifies each archive before reading selected package members and
does not install packages or execute npm lifecycle scripts. Supply `--node` if
Node.js is not on `PATH`. To check either retained record without the archives
or Node, pass its path as `--output` together with `--check`.

The [earlier repair](../included/repaired/skills/by-category/coding-refactoring-repository-automation/selected-structure-reference/nextjs-turbopack/SKILL.md)
and its 16.4.3 build and analysis evidence remain unchanged. The new overlay has
not been tested in an independent matched agent trial.
