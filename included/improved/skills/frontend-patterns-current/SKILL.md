---
name: frontend-patterns-current
description: Implement or review React UI behavior, asynchronous requests, effect cleanup, accessibility and measured rendering changes. Use when a frontend task involves those contracts; preserve the app's existing framework and data layer.
license: MIT
---

# Frontend behavior and request lifecycles

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. This experimental overlay
preserves the locked source in `provenance/`; agent efficacy is unbenchmarked.

First identify the supported browser/runtime, framework, data layer and user
flow. Preserve their OS requirements. Installation and host independence do not
authorize an OS port or a replacement framework.

For requests, prefer the framework's loader or existing cache/query library.
An Effect is a synchronization boundary, not a general-purpose data framework.
If a small client-only Effect is justified, define its contracts explicitly:

- Include every response-determining input in a stable key, including relevant
  account/authorization scope. Never put secrets into keys, URLs or logs. Clear
  or partition cached data when that scope changes.
- Check status and validate the response before displaying it. A JSON parser
  does not make an error response successful or establish a TypeScript type.
- Cleanup must prevent late results from replacing newer state. Abort when the
  transport supports it and retain a generation/ignore guard because cancellation
  may be ignored. Cover unmount, key changes, disable and repeated refresh.
- Define whether stale data remains visible during a refresh. Do not display a
  different key's data as current. Keep loading and error state consistent with
  that decision. Do not silently retry mutations or duplicate user actions.
- Inline fetchers and options must not create an Effect/request loop. Stable
  callbacks alone do not solve response races. Keep callback closures current
  without claiming that every function-identity change is a new request.

[request.ts](references/request.ts) is an optional, client-only lifecycle example
with no cache, retries, deduplication, persistence, SSR or callback hooks. Its key
must encode all request inputs. Fetcher identity changes alone do not refetch;
call `refetch` or change the key. Refresh clears previous data. Disabling clears
visible state and aborts owned work; refetch while disabled is a no-op. A failed
request is returned in state, so callers inspect `error`. Its stable `refetch`
uses the most recently committed Effect context. It is not a drop-in replacement
for the source hook's `onSuccess`/`onError` API or a production query library.

For UI work, use native controls and semantic elements first. Verify labels,
keyboard operation, focus order/return, visible focus and meaningful loading,
empty and error states. A menu needs keyboard behavior, not just roles. A modal
needs focus handling and background isolation. Choose a maintained accessible
primitive when the existing stack provides one; do not certify a partial snippet
as an accessible component. Test the actual interaction in supported browsers.

Keep derived rendering pure: copy shared arrays before sorting. Measure before
adding memoization or virtualization; check actual render cost, layout and user
interaction rather than assuming every callback needs `useCallback`. Test
development StrictMode separately: its extra setup/cleanup cycle can legitimately
start and then abort an initial request. Never suppress that behavior to make a
one-request test pass.

Use deferred responses to exercise out-of-order resolution and disable/unmount.
Add representative keyboard and browser checks when changing UI components.
Report component checks separately from agent trials and production readiness.
