# API and backend component controls

Use these checks to inspect selected API, authentication, retry, error-handling,
logging and Go request-decoding examples. The original examples passed 6 of 16
Node controls and 3 of 6 Go controls. The maintained references passed 16 of 16
and 6 of 6. Their compiler, cancellation and cleanup observations are retained
alongside the original failures in `native/`.

These are targeted component regressions. The author had read the skills before
designing them. They do not measure coding-agent success, a complete application,
JWT verification, database consistency, throughput or latency. Identical locked
and inspected upstream excerpts share one source arm. See
[the evidence and scope](../../../docs/research-backend-contracts.md).

To verify the published inputs without installing Node or Go:

```powershell
python benchmarks/component-controls/backend/prepare_backend.py --check
```

To rerun the actual controls on Windows x64, provision the exact Node/npm
dependencies described in [the frontend controls](../frontend/README.md) and
Go 1.27.3. Choose explicit executable paths and a new workspace directly inside
that dependency directory:

```powershell
python benchmarks/component-controls/backend/run_backend_native.py `
  --node <node-executable> --go <go-executable> `
  --dependency-root <dependency-directory> `
  --workspace <dependency-directory/new-backend-controls> `
  --output <new-evidence-directory>
```

The runner checks runtime and direct dependency versions, rejects an existing
workspace, disables Go downloads and telemetry in private state, and retains
stdout, stderr and process cleanup receipts. It compares new observations with
the published results. A compiler failure in the source arm is an expected,
recorded finding; a controller crash or changed result fails the rerun.

`contract.json` distinguishes protocol/SDK requirements from chosen application
semantics. `adapters/` declares the injected framework subset and fixtures.
`source-provenance.json` records the two source aliases and the pre-candidate
development order. `qualification.mjs` adds eight maintained-boundary checks;
they are separate from the 22 comparative controls. The Go reference delegates
schema, required-field, unknown-field and domain validation to its caller.
