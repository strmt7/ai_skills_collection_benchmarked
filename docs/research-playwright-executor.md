# Playwright executor module-path control

The pinned Playwright skill's executor replaces the caller's `NODE_PATH` when it starts a script. On a project that uses that supported Node module lookup mechanism, a script can run directly but fail through the executor because an existing module search directory disappears. Node documents [`NODE_PATH`](https://nodejs.org/api/modules.html#loading-from-the-global-folders) and its platform-specific separator; [`path.delimiter`](https://nodejs.org/api/path.html#pathdelimiter) provides that separator.

The maintained [Playwright package](../included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill/SKILL.md) prepends its own dependency directory while preserving the caller's entries. Install the package in a separate writable directory. The package pins Playwright 1.65.1 and includes executor tests. The original skill and executor are retained in the overlay's provenance folder and the pinned mirror remains unchanged.

## Tested behavior

The [current control](../artifacts/repaired-skill-readiness/playwright-executor-v2/reproduce.py)
used the same Playwright 1.65.1 lock for both executors on Windows x64 and Linux
x64 with Node 24.22.3 and 26.13.1. A fixture module was available only through
two existing module search directories. The direct script resolved the
fixture, the original executor failed to load it, and the maintained executor
resolved it in both file and inline modes. The maintained executor also
resolved its Playwright dependency with `NODE_PATH` unset and launched
version-matched headless Chromium with its sandbox enabled. All four lanes
observed the expected result on an in-memory page.

The scope is executor and browser mechanics. See the
[current results](../artifacts/repaired-skill-readiness/playwright-executor-v2/)
and [earlier 1.64.1 results](../artifacts/repaired-skill-readiness/playwright-executor-v1/).
The [upstream observation](../artifacts/repaired-skill-readiness/playwright-executor-v2/upstream-observation.json)
records a temporary-path documentation change and the unchanged upstream
executor blob.

## Reproduce on Windows

From the repository root with Python 3.11+, Node and npm installed, copy the overlay twice to fresh temporary directories. The original copy receives the pinned upstream executor; both copies use the same tested Playwright lock. The control creates a separate fixture and writes its process output outside the checkout.

```powershell
$probeDir = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $probeDir | Out-Null
$source = 'included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill'
Copy-Item -LiteralPath $source -Destination "$probeDir/original" -Recurse
Copy-Item -LiteralPath $source -Destination "$probeDir/repaired" -Recurse
Copy-Item -LiteralPath "$probeDir/original/provenance/original.run.js" -Destination "$probeDir/original/run.js" -Force
npm ci --prefix "$probeDir/original" --no-audit --no-fund
npm ci --prefix "$probeDir/repaired" --no-audit --no-fund
$env:PLAYWRIGHT_BROWSERS_PATH = "$probeDir/browsers"
node "$probeDir/repaired/node_modules/playwright/cli.js" install chromium --only-shell
py -3.13 artifacts/repaired-skill-readiness/playwright-executor-v2/reproduce.py `
  --node (Get-Command node).Source --original "$probeDir/original" --candidate "$probeDir/repaired" `
  --browsers "$probeDir/browsers" --scratch "$probeDir/scratch" --output "$probeDir/output"
```

Replace the Python invocation if needed. The control checks source bytes, matching package metadata and installed Playwright versions before it runs. It reports failures rather than converting them into passes, and it does not contact an external website.
