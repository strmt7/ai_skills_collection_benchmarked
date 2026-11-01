# Playwright executor module-path control

The pinned Playwright skill's executor replaces the caller's `NODE_PATH` when it starts a script. On a project that uses that supported Node module lookup mechanism, a script can run directly but fail through the executor because an existing module search directory disappears. Node documents [`NODE_PATH`](https://nodejs.org/api/modules.html#loading-from-the-global-folders) and its platform-specific separator; [`path.delimiter`](https://nodejs.org/api/path.html#pathdelimiter) provides that separator.

The maintained [Playwright package](../included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill/SKILL.md) prepends its own dependency directory while preserving the caller's entries. Install it in a separate writable directory, not inside the source mirror. The package pins Playwright 1.64.1 and includes executor tests. The original skill and executor are retained in the overlay's provenance folder and the pinned mirror remains unchanged.

## Tested behavior

In fresh Windows and Linux installations, the [control](../artifacts/repaired-skill-readiness/playwright-executor-v1/reproduce.py) used the same Playwright 1.64.1 lock for both executors and made an ordinary fixture module available only through two existing `NODE_PATH` entries. With Node 24 and Node 26, the direct script succeeded, the original executor failed to find that module, and the repaired executor succeeded for both file and inline scripts. The repaired executor also resolved its own Playwright dependency with `NODE_PATH` unset and completed a real headless Chromium check against in-memory page content. Results are recorded for each platform and Node version in the [component evidence](../artifacts/repaired-skill-readiness/playwright-executor-v1/); raw process output remains in the independent test workspace.

This is a narrow executor test and browser smoke, not a full application test or a coding-agent benchmark. A [separate source observation](../artifacts/repaired-skill-readiness/playwright-executor-v1/upstream-observation.json) records that the newer upstream commit improved temporary-path documentation while keeping the same executor blob. The complete upstream update has not been reviewed or adopted.

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
py -3.13 artifacts/repaired-skill-readiness/playwright-executor-v1/reproduce.py `
  --node (Get-Command node).Source --original "$probeDir/original" --candidate "$probeDir/repaired" `
  --browsers "$probeDir/browsers" --scratch "$probeDir/scratch" --output "$probeDir/output"
```

Replace the Python invocation if needed. The control checks source bytes, matching package metadata and installed Playwright versions before it runs. It reports failures rather than converting them into passes, and it does not contact an external website.
