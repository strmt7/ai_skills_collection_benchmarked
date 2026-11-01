# Playwright response-ordering control

The mirrored E2E skill waits for a search response after filling the input. A fast response can arrive before the listener is registered. Playwright's [response-wait example](https://playwright.dev/docs/api/class-page#page-wait-for-response) registers the wait before the triggering action. Its [load-state guidance](https://playwright.dev/docs/api/class-page#page-wait-for-load-state) discourages using `networkidle` as a general testing-readiness signal.

The maintained [E2E testing overlay](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md) demonstrates matching the method, path, and query before filling the input, checks the HTTP status, and recommends a separate retrying assertion on the rendered result. Adapt the example to the application's actual behavior. The pinned mirror and original text remain unchanged.

## What the control measures

The [control](../artifacts/repaired-skill-readiness/e2e-response-v1/control.cjs) executes the hash-checked method bodies from the original and the overlay after removing their TypeScript parameter annotations. It also runs a variant that changes only the ordering of the original response wait and action. A local HTTP server returns a response on each input event. The page performs 100 ms of synthetic synchronous work after starting the request; this creates a timing-sensitive case and is not intended to represent a typical production workload. Each condition runs ten times in rotated order with a 1.2-second Playwright timeout. The server must receive all 31 requests, including the final HTTP 500 case. The overlay also checks the rendered result and rejects that error response.

| Platform | Node | Original | Ordering only | Overlay |
| --- | --- | ---: | ---: | ---: |
| Windows | 24.22.2 | 9/10 | 10/10 | 10/10 |
| Windows | 26.13.0 | 10/10 | 10/10 | 10/10 |
| Linux | 24.15.0 | 6/10 | 10/10 | 10/10 |
| Linux | 26.13.0 | 8/10 | 10/10 | 10/10 |

These are individual synthetic component runs using Playwright 1.64.1 and headless Chromium 156.0.8078.4, not a reliability estimate or a coding-agent benchmark. Scheduling affects whether the original fails. The checks do not establish that an agent using the skill performs better.

The source lock is commit `846ffb75da9a5f4e677d927af1ad4a1951652267`. A separate [source observation](../artifacts/repaired-skill-readiness/e2e-response-v1/upstream-observation.json) records the same method in upstream commit `b38be6a7f6350964d59328b52f0624e1d1d552d1`; the Node 26 controls for that method are retained with the other [recorded results](../artifacts/repaired-skill-readiness/e2e-response-v1/). This is a review of that method only, not adoption or review of the complete upstream update.

## Reproduce on Windows

From the repository root, with Node and npm installed, create a fresh temporary installation, copy the retained Windows lock, and install its packages and browser there:

```powershell
$testDir = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $testDir | Out-Null
Copy-Item artifacts/repaired-skill-readiness/e2e-response-v1/locks/windows/package*.json $testDir
npm ci --prefix $testDir --no-audit --no-fund
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path $testDir 'browsers'
node "$testDir/node_modules/playwright/cli.js" install chromium --only-shell
node artifacts/repaired-skill-readiness/e2e-response-v1/control.cjs `
  included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md `
  included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md `
  $testDir
```

The installation and browser download remain outside the checkout. The control verifies the exact normalized skill hashes before executing their example methods and reports the lockfile digest, runtime versions, results, and negative control as JSON. Its output varies with scheduling; a passing original run does not disprove the race. Linux lock and result files are retained as well.
