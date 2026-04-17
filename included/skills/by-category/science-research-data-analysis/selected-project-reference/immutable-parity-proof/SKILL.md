---
name: immutable-parity-proof
description: Produce content-addressed parity evidence and protect the frozen upstream snapshot while porting or verifying native surfaces.
origin: repo-local, grounded in official GitHub Actions artifact and benchmark guidance
---

# Immutable Parity Proof

Use this skill whenever a parity claim, frozen-snapshot claim, or native-C++
claim is about to be made.

## Required checks

1. Verify the frozen snapshot manifest with:
   `.venv/bin/python scripts/frozen_source_manifest.py --verify`
2. Run differential tests against the frozen snapshot on identical inputs.
3. Prefer content-addressed comparisons:
   - serialized output trees for store-backed paths
   - patched outbound call payloads for external side effects
   - stable JSON-like outcome snapshots for deterministic object behavior
4. If the change touches `cpp/`, scan the native tree with:
   `.venv/bin/python scripts/check_native_cpp.py --all`
5. Treat any embedded-Python execution in `cpp/` as native-debt, not as fully
   converted C++ coverage.

## Reporting rule

- State the manifest verification result.
- State the exact parity suites that ran.
- If a surface is still wrapper-heavy or depends on embedded Python in `cpp/`,
  do not count it as native-converted coverage.
