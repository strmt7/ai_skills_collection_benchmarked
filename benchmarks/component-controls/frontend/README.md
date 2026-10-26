# Frontend component controls

These are eight targeted correctness contracts for selected TypeScript/React
excerpts, **not AI-agent trials or whole-skill scores**. The author read the
examples before defining the contracts; this is not a blinded holdout. Expected
behavior comes from the primary API sources and explicit application choices in
[`contract.json`](contract.json). Do not use this table to claim an advantage over
GPT, Karpathy, an upstream collection or a production query library.

| Excerpt arm | Contracts met | TypeScript check |
| --- | ---: | --- |
| Locked ECC `846ffb75` | 1 / 8 | Fails: removed Zod `.errors` |
| Upstream ECC `f3904009` | 3 / 8 | Fails: removed Zod `.errors` |
| Maintained experimental examples | 8 / 8 | Passes |

The upstream sort-copy and callback-identity fixes account for its two additional
passes. Both upstream revisions still lose the fetch failure's cause and accept
stale query results under the chosen lifecycle contract. HTTP status handling
already passes in all three arms. The maintained hook also passed the separate
[`lifecycle.mjs`](lifecycle.mjs) qualification, including real development
StrictMode, cancellation, non-Error rejection, disabled refresh and unmount.

[`result.json`](result.json) binds exact inputs, native output, compiler logs and
process exit receipts. `native/` preserves failed checks, not just passes.
CI runs `python benchmarks/component-controls/frontend/prepare.py --check` to
detect changed inputs or inflated summaries. A separate Windows job uses
`run_native.py` to rerun Node and compare actual observations. Neither establishes
agent behavior. The harness intentionally exits zero when it successfully records
component failures; inspect the individual boolean results and compiler exits.

## Reproduce the recorded Windows x64 cohort

Use a new, isolated dependency workspace and explicit runtime paths. Provision
Node **26.12.1** and npm **12.2.1** from verified official artifacts; do not change
the global installation. Copy this directory's `package.json` and
`package-lock.json` into that workspace, then run its npm with
`ci --ignore-scripts --strict-peer-deps --engine-strict`. Verify `npm ls --all`
and `npm audit`. The recorded cohort has 63 dependency packages and zero reported
advisories at capture time; that is not a promise about future advisories.

With `<repo>`, `<deps>` and `<node>` replaced by explicit local paths:

```text
python <repo>/benchmarks/component-controls/frontend/run_native.py --node <node> --dependency-root <deps> --workspace <deps>/controls-new --output <new-output-directory>
```

That Windows runner owns each process tree, checks the installed cohort and
compares actual observations with the recorded contracts. To inspect individual
steps in a different new workspace:

```text
python <repo>/benchmarks/component-controls/frontend/prepare.py --workspace <deps>/controls-new
<node> <deps>/node_modules/typescript/bin/tsc --ignoreConfig --module NodeNext --target ES2022 --lib ES2022,DOM --types react --strict --noEmitOnError false --outDir <deps>/controls-new/compiled <deps>/controls-new/locked.mts
<node> <repo>/benchmarks/component-controls/frontend/controls.mjs <deps> <deps>/controls-new/compiled/locked.mjs
```

Repeat the last two commands for `upstream` and `maintained`. Compile diagnostics
are evidence: do not stop or alter source to make the locked/upstream arms compile.
Emission despite type errors is deliberate, allowing the independent runtime
controls to observe those excerpts. Run `lifecycle.mjs` with the maintained module
and the same arguments. Use bounded process ownership; the recorded run used the
repository's Windows job controller with no surviving owned processes.

`prepare.py` adds only declared React/Zod imports and small invocation wrappers.
The hook and fetch bodies are copied unchanged from pinned text; the sort return
expression and Zod accessor are extracted without rewriting. Exact locked text
is in the overlays' provenance, and compared upstream text is in `fixtures/`,
with its MIT notice in `LICENSE`. No original PASS/FAIL labels serve as an oracle.
There is no network fetch, external script execution or browser profile in the
controls. jsdom does not establish real-browser or accessibility readiness.

Only Windows x64 was executed for this cohort. This work adds no OS port and
does not alter Crawl4AI's Windows requirement. See the
[research record](../../../docs/research-frontend-contracts.md) for scope and open
qualification work.
