# External Benchmark Adapter Smoke Results

These historical probes checked registry declarations and repository resolution. Their percentages count those checks; they do not measure task success, native adapter execution or model performance.

The old `adapter_ready` status is retained verbatim. Older captures did not record the successful tree transport, so their commit-to-tree binding cannot be retrospectively established from those records alone. New probes retain transport evidence and verify the requested commit when using Git fallback.

## Summary

- Run: `2026-11-09-expanded-benchmark-source-probes`
- Methods checked: `6`
- Methods passing declaration/source checks: `6`
- Methods with failed checks: `0`

## Results

| Method | Legacy status | Metadata checks (%) | Recorded HEAD | Artifact |
|---|---|---:|---|---|
| `swe-skills-bench` | `adapter_ready` | 100.0 | `4d3450d9216a590a8726fcb3604b5143daca776b` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/swe-skills-bench/artifact.json` |
| `terminal-bench` | `adapter_ready` | 100.0 | `cfc7b6c66f2c731e4b70d92ee71ee5d6d3b55b64` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/terminal-bench/artifact.json` |
| `swe-bench-pro-v2` | `adapter_ready` | 100.0 | `66f92766bba642462d4bbe5479e83f91f9211862` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/swe-bench-pro-v2/artifact.json` |
| `deepswe` | `adapter_ready` | 100.0 | `0b9fabbb63b9104d678fe965e1632f2dd9eaa2ea` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/deepswe/artifact.json` |
| `workarena` | `adapter_ready` | 100.0 | `e885130962f61fb64ac305497996a46cfc7d18f0` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/workarena/artifact.json` |
| `scienceagentbench` | `adapter_ready` | 100.0 | `c26e151ed601ba109dc4d35e057ff8e73fec469d` | `artifacts/external-benchmark-integrations/2026-11-09-expanded-benchmark-source-probes/scienceagentbench/artifact.json` |
