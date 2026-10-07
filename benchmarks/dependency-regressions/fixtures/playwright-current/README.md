# Frozen Playwright API controls

Copy this directory into a new temporary workspace, then run `npm ci
--ignore-scripts` there with the verified Node/npm toolchain. The graph pins
Playwright Test 1.63.0, TypeScript 7.0.2 and Node types 26.6.4. Installation is
explicit; the control runner never installs dependencies or browsers.

From the repository root:

```text
node benchmarks/dependency-regressions/playwright_type_controls.mjs --package-root <workspace> --output <new-receipt.json>
```

The negative fixture must fail only for the two unsupported options. The
positive fixture must compile without diagnostics. A compiler infrastructure
failure cannot count as a successful negative control. These are API contract
checks, not browser tests or agent benchmark scores. The independent browser
scheduling controls live in `playwright_wait_controls.mjs`.

The fixtures are maintained by this project. Installed Playwright, TypeScript
and Node type dependencies retain their own licenses and notices; the lockfile
records their complete resolved graph and integrity values.
