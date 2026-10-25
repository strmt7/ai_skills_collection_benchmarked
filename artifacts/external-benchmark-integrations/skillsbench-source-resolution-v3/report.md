# External Benchmark Adapter Smoke Results

These historical probes checked registry declarations and repository resolution. Their percentages count those checks; they do not measure task success, native adapter execution or model performance.

The old `adapter_ready` status is retained verbatim. Older captures did not record the successful tree transport, so their commit-to-tree binding cannot be retrospectively established from those records alone. New probes retain transport evidence and verify the requested commit when using Git fallback.

## Summary

- Run: `skillsbench-source-resolution-v3`
- Methods checked: `1`
- Methods passing declaration/source checks: `1`
- Methods with failed checks: `0`

## Results

| Method | Legacy status | Metadata checks (%) | Recorded HEAD | Artifact |
|---|---|---:|---|---|
| `skillsbench` | `adapter_ready` | 100.0 | `f860ecf02ef53412a030f8661c83d644b739ff01` | `artifacts/external-benchmark-integrations/skillsbench-source-resolution-v3/skillsbench/artifact.json` |
