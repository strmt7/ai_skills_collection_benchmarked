---
name: benchmark-first
description: Benchmark converted code against the frozen upstream implementation before making performance claims.
origin: repo-local
---

# Benchmark First

Use this skill after parity has been demonstrated for a converted surface.

## Rules

- Compare the upstream implementation and the converted implementation on the
  same inputs and same machine class.
- Verify parity on the exact benchmark input before timing it.
- Prefer representative real data. If real data is unavailable, document the
  synthetic fallback clearly.
- Use the narrowest suite, group, and match filters that isolate the edited hot
  path before widening to larger reports.
- Run repeated measurements and report medians or geometric means, not one-off
  wall-clock numbers.
- Report version and environment details with the results.
- If the benchmark points to boundary overhead instead of native arithmetic,
  load `cpp-performance-optimization` before changing code.
