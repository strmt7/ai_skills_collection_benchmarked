---
name: webapp-testing-current
description: Verify a specific local web application with smoke tests, browser actions, screenshots or console diagnosis. Use the project's test runner and a verified application instance.
license: Apache-2.0
metadata:
  source: anthropics/skills
  revision-status: experimental-unbenchmarked
---

# Verify a local web application

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions. Establish the intended application and origin,
the user action, and its observable result. Use disposable data for writes.

## Run against the intended instance

Use the project's existing runner and lockfile. Discover the declared runtime
and provision missing dependencies through the project's locked setup in an
isolated workspace. Use the matching browser for UI checks.

Prefer the project's managed test server. For Playwright Test, the
[managed server example](references/playwright-managed-server.md) shows how to
start a project-declared command, wait for an HTTP readiness URL, refuse an
occupied endpoint, and assert the actual instance in the test. Match the
readiness contract to the application. Verify any explicitly supplied server
before interacting with it and leave that server under its owner's control.

For a newly started server, retain process ownership, bound startup and
capture diagnostics without blocking the child. Confirm a meaningful
application response, then verify that the owned process tree and listeners
close on success, failure and cancellation.

## Verify the user outcome

Wait for the relevant rendered condition with a retrying locator assertion.
Prefer accessible roles and names or a stable test ID from the application's
contract. Use the target control or result as the readiness signal when
background traffic continues.

Register a response, download or popup wait before the action. Identify the
expected event independently of success, then assert its status and the
resulting UI. Check the application state before retrying an action with an
uncertain outcome. Evaluate expected error states against the same product
contract as successful ones.

Use a fresh context and the requested viewport matrix. Capture console and
page errors before navigation when they matter. Store traces and screenshots
in a run-owned directory and review them as evidence alongside assertions.
Close acquired contexts and browsers even when the check fails. Report
observed outcomes, skips and cleanup failures with useful artifact paths.

The [controls and limits](references/controls.md) record the verified server
behavior and the platform and evaluation scope.
