---
name: pybind11-runtime-parity
description: Legacy reference only. Current main does not use pybind11 ports; use this only to understand old debt before removing it.
origin: repo-local, grounded in official pybind11 docs
---

# pybind11 Runtime Parity

Do not use this skill to add new code in current `main`. The active
architecture is standalone native C++ plus optional C ABI interop. If old
pybind debt is encountered, remove or replace it rather than extending it.

This file remains only as a historical warning about the classes of runtime
behavior that made old binding ports unsafe.

## Rules

- Preserve frozen-upstream behavior before simplifying the C++.
- Catch `py::error_already_set` for exceptions that originate in Python code or
  Python C API calls; do not assume pybind11 C++ exception wrappers catch them.
- Use Python truth-value evaluation for generic Python objects instead of
  forcing `py::cast<bool>`.
- Avoid storing pybind11 objects as long-lived members in native structs unless
  the GIL and lifetime implications are explicitly understood and unavoidable.
- When implementing iterator behavior, use `pybind11::stop_iteration` or
  equivalent Python iterator semantics rather than ad-hoc sentinels.
- If the binding depends on imports from partially ported modules, make that
  dependency explicit and local to the wrapper instead of hiding it.
- If performance work touches the boundary, prefer typed buffers or native
  structs over repeated Python-object lookups in hot loops.

Read `references/official-guidance.md` only when removing or auditing old
binding debt. New interop belongs in `cpp/api/` as raw C ABI buffers and JSON,
not pybind runtime objects.
