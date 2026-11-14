# Modern Node benchmark replay

Prepare a reproducible Node runtime for development experiments when the
publisher's Node image cannot be retrieved. This is an explicitly modified
environment, not a reproduction of the publisher's Node 20 or Node 22 images.

From the repository root on Windows x64:

```powershell
.\dev.ps1 python tools/prepare_native_node_replay.py --runtime .venv/benchmarks/publisher-base-runtime.json --output .venv/replays/node26-1
.\dev.ps1 python tools/prepare_native_node_replay.py --check --output .venv/replays/node26-1
```

The first command needs a [qualified local Linux AMD64 engine and publisher-base
runtime declaration](../../docs/native-benchmark-controller.md). Its paths must
describe the current host. The tool verifies that engine and the pinned base,
then downloads and installs its exact Node and crane distributions privately.
The managed frontend supplies Python automatically. No global package installer,
shell profile, build daemon, registry push or model request is used.

Allow at least 3 GiB of free space. Setup uses a new output directory, preserving
partial files and diagnostics if it fails. Choose another directory for a new
attempt; it never replaces an existing installation. Native assembly is limited
to 512 MiB and six minutes. Smoke tests use an unprivileged account in a leased,
network-disabled container with 512 MiB, one CPU and no automatic restart.

Successful setup writes `runtime.json` for the benchmark controller and
`result.json` with retained source snapshots, complete file hashes and actual Node, npm
and npx probe results. The image preserves every base layer and adds the official
Node distribution, a PATH entry and a stable provenance label. Its assembly tag
is removed by updating only the existing manifest bytes before verified loading.
Generated archives and local engine declarations stay in `.venv`.

`--check` performs offline artifact verification. It does not repeat engine or
runtime probes and cannot establish that the engine is currently available.
Neither command qualifies task dependencies, evaluator stages or model gains.
Use the same declared environment in every experimental condition.

The [pins](pins.json) identify Node 26.13.1 with npm/npx 11.20.0, crane 0.22.1 and
the exact publisher base. Archive digests were checked against the official Node
checksum file and both the GitHub release asset digest and crane checksum file.
The complete crane distribution retains its Apache-2.0 license; Node's license
remains inside the generated layer. Source references are in
[source.json](source.json). A pin update requires new installation, failure,
cleanup and reproducibility controls before promotion.
