# Test out-of-order results

Use this check when the user can change a query, filter, or selection while an
earlier request is still running. First confirm the product's intended behavior.
A directory might keep the results for the newest query. A stream that appends
independent events needs a different contract.

1. In an isolated test context, route requests to owned fixtures. Hold the first
   request once it reaches the route. Start the second intent through the UI and
   confirm that its request reaches the route as well. Distinguish the requests
   by their input or an explicit operation identifier.
2. Return the second result first. Wait for the UI to show its expected content.
   Give the two fixtures distinct results so a stale update is observable.
3. Return the first result. Observe that the application finished handling it,
   then check that the UI still shows the second result. A completed HTTP
   response can precede asynchronous application work. Use an existing settled
   status, an observable cancellation, or a narrow test-fixture signal that
   fires after the handler finishes. Keep the final assertion on visible state.

If the application cancels superseded requests, verify that cancellation
explicitly. An aborted request does not exercise handling a late successful
response. Cover both behaviors when either schedule can occur. If two requests
can carry the same query with different results, include a case that
distinguishes the operations instead of comparing query strings alone.

Use a bounded wait for each observed event. Confirm that the test fails against
a known stale-write defect or controlled negative fixture. Fixed sleeps make
races harder to diagnose, and checking only the first visible success can miss
the overwrite.
