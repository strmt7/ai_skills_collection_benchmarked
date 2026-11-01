---
name: e2e-testing
description: Design and run reliable Playwright end-to-end tests with observable outcomes and project-specific fixtures.
---

# End-to-end testing with Playwright

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Start with a user-visible behavior and the project's existing test runner, scripts, browser configuration, and fixture conventions. Use isolated test data, stable selectors that reflect the application's actual interface, and retrying assertions on observable results. Exercise meaningful failure paths and clean up test-owned state. Do not assume particular routes, counts, wallets, services, accounts, or deployment targets exist.

When a test needs a particular response, register the response wait before the triggering action. For an application that really sends a search request on input, an illustrative page-object method is:

```typescript
async search(query: string) {
  const [response] = await Promise.all([
    this.page.waitForResponse(resp => {
      const url = new URL(resp.url())
      return resp.request().method() === 'GET' && url.pathname === '/api/search' && url.searchParams.get('q') === query
    }),
    this.searchInput.fill(query),
  ])
  if (!response.ok()) throw new Error(`Search failed: ${response.status()}`)
}
```

Use the application's real URL, action, and expected status; if results are local or debounced, choose a matching observable condition instead. After the action, assert the rendered result with Playwright's retrying `expect` rather than assuming the response alone proves correct behavior. Avoid fixed sleeps and generic `networkidle` as readiness signals. Respect existing project timeouts rather than prescribing one for every application.

Run the focused test first, then the relevant project suite and browser coverage required by the change. Capture failures using the project's configured traces, screenshots, and reports; preserve their scope and explain retries, skips, and unavailable environments. A retry can help diagnose flakiness but does not make its cause fixed. Report actual results without claiming that passing tests prove the absence of defects.

The original upstream skill is preserved at `provenance/original.SKILL.md`. This maintained overlay corrects selected response-ordering and readiness guidance. Component controls do not measure agent effectiveness.
