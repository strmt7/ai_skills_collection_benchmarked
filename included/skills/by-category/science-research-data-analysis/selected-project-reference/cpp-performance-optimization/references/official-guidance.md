# Native C++ Performance Guidance

- Use typed native data and contiguous memory in hot paths. Keep generic JSON
  or string conversion at the API edge, not inside loops.
- Prefer pre-sized vectors, `reserve`, move-friendly construction, and
  stack/compile-time constants for genuinely static data.
- Avoid repeated filesystem scans, metadata parsing, dynamic allocation, and
  serialization on the success path.
- Use C ABI buffer entrypoints for external array consumers when the contract
  allows it. The C++ side should see pointers, lengths, shapes, and explicit
  ownership, not package objects.
- Benchmark tuning should reduce machine jitter and use stable CPU-frequency
  settings before trusting fine-grained timing comparisons.

Repo-validated heuristics that also align with the reviewed external guide:

- remove repeated scans and heap churn before chasing micro-arithmetic wins
- prefer contiguous data layouts in hot iteration paths
- precompute reused loop invariants outside the hottest loop
- prefer move-friendly construction and reserved capacity over repeated copies
- consider compile-time constants only for truly static data
- use zero-copy views only when object lifetime is proven safe
- simplify hot-loop control flow only when parity and error timing stay exact
- parallelize only when ordering, numeric behavior, and exception timing remain
  parity-clean under test

Primary references:

- https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines
- https://en.cppreference.com/w/cpp/container/vector/reserve
- https://en.cppreference.com/w/cpp/language/move_constructor
- https://pyperf.readthedocs.io/en/latest/system.html
