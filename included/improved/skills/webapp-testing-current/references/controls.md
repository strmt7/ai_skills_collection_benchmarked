# Controls and limits

## Original package

Linux controls of the locked `with_server.py` reproduced an unrelated port
being accepted after the intended process exited, a noisy child blocking on
undrained output, and a child surviving termination of its shell. The helper
preserved a failing test command's exit status. The independent fixture
removed the processes it started. [Original control results](../../../../../artifacts/research/2026-10-02/webapp-server-runtime-controls-v2.json)

The older browser controls reproduced late response subscriptions, stale
immediate counts and a network-idle timeout while the intended UI was ready.
The primary references explain current locator actionability and retrying
assertions. [Locator actionability](https://playwright.dev/docs/actionability) · [Retrying assertions](https://playwright.dev/docs/test-assertions)

## Maintained example

The exact supplied configuration and instance test are exercised by a
separate native HTTP fixture. Its independent expected outcomes cover normal
startup, noisy startup, delayed readiness, an occupied endpoint, a wrong
instance, a failed child, a startup timeout and interruption. The recorded
runs use Playwright Test 1.65.1 and verify the outcome and owned cleanup after
each case. [Source-bound service controls](../../../../../artifacts/research/2026-11-25/webapp-managed-service/review.json)

The service controls exercised the Linux lifecycle in an isolated container.
Native Windows teardown and agent effectiveness remain open.

For an independent replay, use an owned Linux environment and stage the two
example files. Save the [contract](../../../../../benchmarks/dependency-regressions/webapp_managed_service_contract.json)
as `service-lifecycle-contract.json` and the observations' `npm_admission`
object as `admission.json`. Verify and stage the three npm archives named in
that record. Run the [fixture](../../../../../benchmarks/dependency-regressions/webapp_managed_service_fixture.py)
with the staging directory, the verified Node executable, and `forward` or
`reverse` as its arguments.
