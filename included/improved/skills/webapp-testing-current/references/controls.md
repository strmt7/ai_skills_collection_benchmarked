# Controls and limits

The original `with_server.py` was exercised unchanged in the project's qualified
Python 3.14.8 Linux container, with no external network and verified container
cleanup. An unrelated listening socket accepts a server command that exits 7;
the test command still runs. A noisy child blocks before binding because its
stdout pipe is not drained. Terminating the helper's shell leaves that live
child running. The independent fixture kills its owned process group afterward.
The helper does preserve a test command's exit status of 11.

Public reproducers: `benchmarks/dependency-regressions/webapp_server_controls.py`
and `webapp_server_fixture.py`. Receipt: `webapp-server-runtime-controls-v2.json`
under `artifacts/research/2026-10-02/`. These are contract controls, including
successful reproductions of defects; they are not skill runtime pass rates.

The existing actual Playwright 1.63.0 browser controls reproduce missed response
subscriptions, stale immediate counts and network-idle timeout despite ready UI.
Public compiler fixtures separately reject unsupported options and accept the
current APIs under TypeScript 7.0.2. They do not execute a browser.

The latest upstream webapp-testing package at
`8a1541c4a3ffa5a20a5a91de0dcf3f0bab1d1ef4` changes its license attribution but
retains the reviewed entrypoint, helper and example behavior. This overlay
changes agent instructions; it does not repair that supervisor, qualify Windows
cleanup, or establish independent agent gains.

Use current official references when qualifying an implementation:
[Playwright readiness](https://playwright.dev/docs/api/class-page#page-wait-for-load-state),
[retrying assertions](https://playwright.dev/docs/test-assertions), and
[Python subprocess pipe/cleanup contracts](https://docs.python.org/3/library/subprocess.html).
