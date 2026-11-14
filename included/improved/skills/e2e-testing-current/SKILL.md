---
name: e2e-testing-current
description: Build or repair Playwright end-to-end tests, page objects, readiness checks and CI diagnostics. Use for browser journeys and flaky test investigation; preserve the application's real contracts and existing runner.
license: MIT
---

# Reliable browser journeys

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. This maintained derivative
is unbenchmarked for agent efficacy; original guidance remains in `provenance/`.

## Establish the test contract

Inspect the actual journey, expected outcomes, existing runner, lockfile, browser
matrix and test data. Cover the important successful path and a meaningful
failure or empty state. Derive expected results from product requirements or
independent fixtures. A screenshot, HTTP success or nonzero result count alone
does not establish that the intended behavior occurred.

Use the project's declared runtime and matching Playwright/browser versions.
Discover installations; provision missing dependencies through its locked setup
in an owned environment. Do not replace the runner, install global packages or
silently download a different tool through an unpinned command.

## Synchronize with observable behavior

- Assert the relevant UI state with awaited, retrying locator assertions.
  Prefer roles and accessible names when they identify the intended control;
  use stable test IDs where those are the application's contract. Match list
  content or counts with `toHaveText` or `toHaveCount` when they can change;
  an immediate `count()` observation does not retry an assertion.
- Treat navigation completion and business readiness separately. Polling can
  prevent network idleness while the page is usable. Wait for the actual
  heading, results, enabled control or application readiness signal. Neither
  `networkidle` nor an arbitrary sleep is a general test-readiness contract.
- Register a necessary event wait before its triggering action. Match request
  identity precisely enough to exclude background traffic: origin, path,
  method and relevant query/body correlation. Observe the matching response,
  then assert its status and the resulting UI. Filtering the waiter to status
  200 can turn an actual HTTP error into an unhelpful timeout.
- Keep page objects small. Centralize repeated selectors and interactions while
  leaving the test's business expectations visible. Do not add a page-object
  framework or extra waits around every auto-waiting action.

For example, adapt this contract to the actual application's API and UI:

```typescript
import { test, expect } from '@playwright/test'

test('search displays the expected item', async ({ page, baseURL }) => {
  if (!baseURL) throw new Error('Configure the owned application baseURL')
  const origin = new URL(baseURL).origin
  await page.goto('/items', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: 'Items', exact: true })).toBeVisible()
  const query = 'alpha'
  const [response] = await Promise.all([
    page.waitForResponse(response => {
      const url = new URL(response.url())
      return url.origin === origin && url.pathname === '/api/search' &&
        url.searchParams.get('q') === query && response.request().method() === 'GET'
    }),
    page.getByTestId('search-input').fill(query),
  ])
  expect(response.status()).toBe(200)
  await expect(page.getByTestId('item-card')).toHaveText([query])
})
```

## Diagnose failures and own resources

Reproduce a failure with retries disabled. Use targeted repetitions when they
test a specific race hypothesis. Preserve the first failure and distinguish
failed, retried, flaky and skipped tests. Do not skip a failing critical journey
in CI, add retries or raise timeouts merely to obtain a green result. Explain
any explicitly approved quarantine and keep its failed behavior visible.

Keep each test's mutable state isolated. Use a declared application endpoint and
an owned server lifecycle; do not accidentally reuse another task's localhost
server. Bound workers and browser projects to the available resources. Close
owned contexts, browsers, listeners and server processes in failure paths too.

Retain useful failure evidence with the test runner's unique output paths and
attachments. Fixed shared screenshot names can collide under parallel runs.
Use runner-managed Playwright traces; for standalone API controls use
`context.tracing.start()` and `stop()`. Chromium performance tracing is a
different artifact. Verify that requested traces, screenshots and reports were
actually produced, and report browser/platform coverage and remaining skips.

See the official [page APIs](https://playwright.dev/docs/api/class-page) and
[retrying assertions](https://playwright.dev/docs/test-assertions) for the
project's supported version. Component controls validate selected mechanisms;
they do not establish a model-performance gain or complete upstream readiness.
