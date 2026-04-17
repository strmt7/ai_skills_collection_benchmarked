---
name: cpp-parity-porting
description: Port one upstream ome-zarr-py surface to standalone native C++ without touching the frozen snapshot.
origin: repo-local
---

# C++ Parity Porting

Use this skill when converting an upstream Python module or helper.

## Workflow

1. Read the upstream implementation from `source_code_v.0.15.0/`.
2. Keep semantics in `cpp/native/`. Use `cpp/tools/` for standalone executable
   entrypoints and `cpp/api/` only for a thin C ABI over already-native
   semantics.
3. Port behavior first, including exception types and messages when they are
   observable.
4. Do not add Python-object semantics. If the upstream surface is hard to
   model because it depends on Python runtime behavior, keep that behavior in
   the frozen development oracle until a native model is designed and tested.
5. Load `immutable-parity-proof` before making any parity or native-coverage
   claim.
6. Add differential tests against the upstream snapshot.
7. If the observable output includes absolute paths and the surface is
   read-only, run the upstream and converted implementations against the same
   fixture path to avoid false stdout mismatches.
8. Do not keep Python-object semantics in C++ implementation code. Optional
   interoperability belongs in `cpp/api/` as raw buffers and JSON, not as
   pybind or CPython object dispatch.
9. After parity holds, load `benchmark-first` and
   `cpp-performance-optimization` before making performance changes.
10. Do not describe a surface as pure-native unless the semantics live in
    `cpp/native/`.
