# Browser testing package review

Reviewed all six original webapp-testing resources and all four original
standalone Playwright resources: complete entrypoints, helper/executor source,
examples, dependency declarations and packaged license. Resource-level progress
records bind each review to exact file bytes; reviewed text is not independently
qualified implementation or agent efficacy.

## Webapp-testing

The entrypoint mandates network idle before inspecting dynamic UI and prohibits
source inspection until customized execution is necessary. A helper should be
assessed before being trusted for lifecycle or security contracts. The earlier
actual browser controls already demonstrate that network idle can time out
while the relevant UI is ready. Fixed sleeps in examples also do not assert the
expected effect. The examples assume `/tmp` and `/mnt/user-data/outputs` exist,
construct file URLs by interpolation rather than a portable URI API, and close
browsers only on the success path. Console capture is registered before navigation,
which is appropriate; event capture alone is not an application correctness test.

The complete server helper polls TCP only, does not verify process liveness or
application identity, starts shell commands with undrained stdout/stderr pipes,
and terminates the shell rather than its process tree. Actual bounded Linux
controls reproduce an unrelated listening port accepting `exit 7`, a noisy
child blocking before bind, and a live child surviving helper cleanup. A
negative test command's status 11 is correctly propagated. The fixture captures
actual child process state and kills only its own process group; the isolated
backend verifies container cleanup. No user server was touched.

`webapp-server-runtime-controls-v2.json` qualifies the current public reproducer.
The earlier receipt is retained before the added live-state observation. These
controls are not four runtime benchmark passes for the skill. The current
upstream package at `8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4` changes the license's
copyright line to Anthropic 2026; normalized full-file comparison leaves the
entrypoint, three examples and helper unchanged. Original mirrors are retained.

An explicit Apache-2.0 `webapp-testing-current` overlay replaces these
instructions with application-specific readiness, controlled actions, real
assertions, owned process cleanup and truthful reporting. It includes exact
original provenance. It does not silently repair the supervisor or claim
Windows lifecycle qualification or agent gains.

## Standalone Playwright

The original four-file package advertises an absent `API_REFERENCE.md`, declares
Node >=14 despite its newer Playwright dependency, and has no complete lockfile.
It implicitly installs dependencies when execution starts. Its wrapper changes
cwd, copies code into installation-local timestamped files, uses substring
heuristics to decide whether to wrap code, and deletes all matching temporary
execution files on the next invocation without ownership tracking. These can
break caller-relative files, read-only installations and concurrent scripts.

Helper readiness and authentication catch failed waits and resolve. Custom
context options overwrite the previously merged environment headers. Browser
launch adds sandbox-disabling flags unconditionally. Click retries can repeat a
mutation after an ambiguous failure. Automatic port detection establishes only
that a service responded; it does not establish the requested application.
Generic cookie acceptance selectors can perform an unintended consent action.

Six public controls reproduce five helper logic schedules through explicit API
doubles, plus a real copied-executor cwd comparison. The doubles do not launch
a browser or prove every application reproduces the chosen schedule. Original
and latest upstream bytes remain unchanged and are hashed before/after probes.

Latest upstream `289abdea7df857dc7a6ece937dbe0c5ecc964ccd`, version 5.0.0,
already removes the unsafe wait/authentication/action helpers, preserves caller
cwd, propagates child exit status, makes installation explicit, preserves merged
headers, adds the reference file, and avoids unconditional sandbox flags for
nonroot users. These are upstream corrections to adopt during the source loop,
not original fixes to credit to this project. Root-mode launch still adds
`--no-sandbox`, and current dependency lock resolves Playwright 1.62.1 instead
of verified latest stable 1.63.0. The license is MIT with lackeyjb's 2025 notice.

The latest reference also imports `@playwright/test` and `axe-playwright` without
declaring them in the standalone package, includes old action v3 examples and
an unsupported `playwright test --slowmo` flag, and mixes browser scripts with
test-runner configuration. Those components need their own declared complete
graph and API qualification; a current entrypoint is insufficient.

## Public compiler controls

The frozen package/lock and original negative/positive TypeScript fixtures now
live in `benchmarks/dependency-regressions/fixtures/playwright-current/`. The
public driver checks staged bytes and direct package identities, bounds compiler
execution, requires exactly the intended two errors, and rejects infrastructure
failures as negative successes. Both current controls pass.

The first public driver attempted an unexported TypeScript 7 subpath and failed
before compilation. That infrastructure failure is preserved separately. The
corrected driver resolves the package's declared `tsc` binary. No results were
invented or failed attempt removed. The existing compiler receipt, browser
receipt and new public replay are different evidence classes.

Primary references: [Playwright readiness and discouraged network-idle use](https://playwright.dev/docs/api/class-page#page-wait-for-load-state),
[Python subprocess pipe and termination contracts](https://docs.python.org/3/library/subprocess.html),
[Node module resolution](https://nodejs.org/api/modules.html#loading-from-node_modules-folders),
and [explicit browser context options](https://playwright.dev/docs/api/class-browser#browser-new-context).

Remaining: actual provider/application workflows, browser coverage of the
standalone current implementation, Windows lifecycle handling, source publication,
other testing-category packages, and independent skill agent comparisons.
