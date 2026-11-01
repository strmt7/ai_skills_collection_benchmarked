---
name: playwright-skill
description: Run focused Playwright browser checks with a portable executor and project-specific targets.
license: MIT
---

# Playwright browser automation

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Identify the user's target, requested interactions, expected outcomes, and the project's existing browser-test setup before running a browser. Use the project's established tests and fixtures when they fit. Do not assume a local port, account, route, data, or server belongs to the task. Start or contact only the intended application and report any missing target or test prerequisites.

For this maintained package, copy the intact skill folder to a writable installation directory outside the source checkout. Run `npm ci` there with a supported Node release; install the required Playwright browser with `npx playwright install chromium`. The lockfile pins Playwright 1.64.1. Use the installed Node and browser versions that your environment and project support. The package's `npm test` exercises its executor without contacting an application.

Run a script with `node <installed-skill-directory>/run.js <script-file>`; the executor keeps the caller's working directory and makes its Playwright dependency available while preserving existing `NODE_PATH` entries. For small checks it also accepts `-e <JavaScript>` with `chromium`, `firefox`, `webkit`, `devices`, and `helpers` preloaded. Close browsers in a `finally` block. For temporary files, use the host's temporary-directory API, such as Node's `os.tmpdir()` and a unique directory; do not assume a fixed machine path. Save scripts or screenshots in a user-selected location when requested.

Prefer locators based on accessible roles and labels, then stable test IDs when the application exposes them. Use Playwright's auto-waiting actions and retrying assertions against observable outcomes. Register response waits before actions that cause them; avoid fixed sleeps and generic network-idle waits as readiness checks. Match selectors, URLs, request methods, and expected statuses to the application being tested.

Use a visible browser when the task or user requires it and a display is available; use headless mode when appropriate for the environment. Run the smallest relevant check first and broaden it when the task requires. Report the target, actions, browser and runtime versions, actual results, and any saved artifact paths. Do not infer overall application quality or agent superiority from a single browser smoke test.

The original upstream skill and executor are preserved in `provenance/`. This maintained overlay changes executor module-path handling and packaging; its component controls do not measure agent effectiveness.
