# Next.js bundler guidance: component controls

The mirrored skill contains version-dependent claims, including a fixed speed range and a suggested `--no-turbopack` switch. The [maintained overlay](../included/repaired/skills/by-category/coding-refactoring-repository-automation/selected-structure-reference/nextjs-turbopack/SKILL.md) asks agents to inspect the project's version, configuration and compatibility before changing bundlers. The original remains in the mirror and in the overlay provenance directory.

The [Next.js Turbopack documentation](https://nextjs.org/docs/app/api-reference/turbopack) describes Turbopack as the default for development and production builds, with `--webpack` to opt into webpack. The [bundle analysis guide](https://nextjs.org/docs/app/guides/package-bundling) documents `next analyze`. Check the documentation for the installed release; these behaviors may change.

With Node 26.13.0, npm 12.2.1 and Next.js 16.4.3, isolated Windows and Linux controls rejected `--no-turbopack` with exit 1. Default and explicit webpack builds exited 0, reported their respective bundlers and generated the expected page. `next analyze --output` exited 0 and its route data included `/`. The Windows control also checked CLI help. The Linux and Windows fixture used the same lockfile. The observations and source hashes are in [the evidence directory](../artifacts/repaired-skill-readiness/next-turbopack-v1/).

These small component checks are not performance measurements or agent evaluations. They do not establish a speed improvement or an advantage over an unassisted agent. The development server itself was not exercised in this control.

## Reproduce on Windows

Use the stated Node and npm versions and run from the repository root. This installs the pinned fixture into a fresh temporary directory. Each app has its own output directory; an existing project is not changed.

```powershell
$fixture = 'artifacts/repaired-skill-readiness/next-turbopack-v1/fixture'
$probeDir = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $probeDir | Out-Null
Copy-Item "$fixture/package*.json" $probeDir
npm ci --prefix $probeDir --no-audit --no-fund
if ($LASTEXITCODE -ne 0) { throw 'npm installation failed' }
foreach ($kind in 'turbo-app', 'webpack-app', 'analyze-app') {
    Copy-Item -LiteralPath "$fixture/project" -Destination "$probeDir/$kind" -Recurse
}
$env:NEXT_TELEMETRY_DISABLED = '1'
$next = "$probeDir/node_modules/next/dist/bin/next"
node $next dev --no-turbopack  # Expected exit: 1 for this tested version.
node $next build "$probeDir/turbo-app"  # Expected: 0; output identifies Turbopack.
node $next build "$probeDir/webpack-app" --webpack  # Expected: 0; output identifies webpack.
node $next analyze "$probeDir/analyze-app" --output  # Expected: 0.
```

Check each exit status as it occurs. Both build outputs should contain `<main>control ready</main>` in `.next/server/app/index.html`; the analysis output's `.next/diagnostics/analyze/data/routes.json` should include `/`. Retain the temporary directory if investigating a discrepancy.
