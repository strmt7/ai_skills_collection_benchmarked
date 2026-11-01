# Bun compatibility and frozen-install controls

The mirrored Bun skill presents the runtime as a drop-in Node replacement and suggests `--frozen-lockfile` for reproducible deployments. Bun implements many Node APIs, but its [compatibility documentation](https://bun.sh/docs/runtime/nodejs-compat) records behavioral differences. Its [install documentation](https://bun.sh/docs/pm/cli/install) also states that a frozen install without any lockfile can install from `package.json` without writing a lock. The maintained [Bun overlay](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime/SKILL.md) asks users to qualify their actual runtime and verify the intended lock exists before relying on a frozen install. The pinned mirror and original text remain unchanged.

## Measured component behavior

On Windows x64 and Linux x64, the retained [frozen-install control](../artifacts/repaired-skill-readiness/bun-runtime-v1/frozen-control.py) ran Bun 1.4.4 against a fresh fixture with no lockfile or pre-existing dependencies. It used a private cache and the public package registry. On both platforms:

| Case | Exit | Lockfile |
| --- | ---: | --- |
| Frozen install, no lockfile | 0 | Not created |
| Ordinary install | 0 | Created |
| Frozen install, matching lock | 0 | Unchanged |
| Frozen install, changed manifest | 1 | Unchanged |

Bun can also use supported non-Bun lockfiles for in-memory migration, so absence of `bun.lock` alone does not prove every project is unlocked. The control deliberately starts with no lockfile of any kind. The [results and process output](../artifacts/repaired-skill-readiness/bun-runtime-v1/) are specific to this fixture and version; package-registry access and the surrounding runtime environment can affect a reproduction.

The [HTTP compatibility probe](../artifacts/repaired-skill-readiness/bun-runtime-v1/http-server-probe.cjs) also observed that `http.createServer() instanceof net.Server` was true with Node 26.13.0 and false with Bun 1.4.4 on both platforms. That demonstrates one compatibility difference, not a general incompatibility rate or performance comparison. Neither control measures coding-agent effectiveness.

The pinned skill describes Bun as implemented in Zig. The selected [upstream observation](../artifacts/repaired-skill-readiness/bun-runtime-v1/upstream-observation.json) at commit `b38be6a7f6350964d59328b52f0624e1d1d552d1` instead notes the Bun 1.4 Rust implementation and warns about compatibility. This is a review of selected passages, not adoption or review of the complete upstream update. [Vercel's current documentation](https://vercel.com/docs/functions/runtimes/bun) calls its Bun runtime beta and describes configuration using `bunVersion` in `vercel.json`; verify the current options and application behavior before deployment.

## Reproduce the frozen-install control

Use a separately installed Bun 1.4.4 executable and Python 3.11 or later. From the repository root on Windows, create new paths for the isolated fixture, cache, and process output:

```powershell
$probeDir = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
py -3.13 artifacts/repaired-skill-readiness/bun-runtime-v1/frozen-control.py `
  --bun 'C:/path/to/bun.exe' `
  --scratch "$probeDir/scratch" `
  --output "$probeDir/output"
```

Replace the executable path and Python invocation with your installation. The script creates the scratch and output directories, installs the fixture packages from the registry, records stdout and stderr, and returns a failure if the observed behavior differs from the four cases above. It does not change a project lockfile. Archive and executable digests from the tested runtimes are recorded with the results.
