---
name: libfuzzer-fuzzing-current
description: Set up, review or debug bounded C/C++ libFuzzer harnesses, sanitizer builds, corpus replay and crash triage. Use when qualifying LLVMFuzzerTestOneInput, diagnosing missing findings or coverage, or choosing reproducible campaign limits and instrumentation.
license: CC-BY-SA-4.0
metadata:
  status: experimental-unbenchmarked
---

# Qualified C/C++ fuzzing

Start with the actual target's format, valid byte domain, documented rejection
behavior and independently defined wrong outcomes. A harness must exercise the
target and make meaningful results observable. Keep harness faults distinct from
target defects. Include empty and malformed inputs when they belong to the API;
do not reject them merely to silence a crash. Reset state between callbacks and
join target threads before returning.

Decode integer fields with a specified byte order or a qualified provider.
Avoid casts that assume alignment and object access. Bound provider fields against
the target's contract, including length, terminator and allocation ownership.
`ConsumeBytesWithTerminator` returns at least its terminator; determine whether
that byte belongs in the target's length. Do not call `free` on an arbitrary
library-owned or differently allocated result.

Verify a supported stable compiler and its matching libFuzzer/sanitizer runtimes
before installing. Record artifact digests and platform. As of 2026-10-07,
LLVM 23.1.3 is the observed stable release; Linux x64 native known-input controls
are qualified here. Other platforms and dependencies need their own checks.
libFuzzer receives important bug fixes; it does not promise major new features.

Instrument target libraries with `-fsanitize=fuzzer-no-link` and the selected
sanitizers; link the final driver with `-fsanitize=fuzzer` and the same toolchain.
Keep target, driver, dependency and sanitizer flags explicit. Do not assume a
macro removes an existing `main`, or mix incompatible compiler runtimes. Verify
the complete build and replay a known instrumented defect plus a valid input.
An unused expression may disappear under optimization; ASan alone does not
detect every undefined arithmetic operation. Preserve production hardening
unless a specific, recorded incompatibility justifies an experiment.

Use an owned disposable environment with explicit wall-clock, per-input, RSS,
allocation, process, input-size, corpus, artifact and output limits. ASan's shadow
address reservation is not RSS. `-rss_limit_mb` bounds resident memory; disabling
it does not repair address-space limits. Check the actual runtime's options.
Do not disable leak detection or continue after memory corruption to manufacture
clean results; record any qualified exclusion separately.

Start with a bounded single-process smoke, then a measured campaign. Choose one
qualified parallel mode and its total resource budget: jobs count campaigns,
workers bound their concurrency, and fork mode adds child processes. Keep crash,
timeout and out-of-memory artifacts distinguishable. A graceful bounded exit is
different from a timeout that kills collection. Record complete raw outcomes.

Pin source, binary, corpus, dictionary and environment identities. Validate
dictionary syntax rather than passing unescaped extracted strings to the parser.
Feature-preserving corpus minimization is not crash-input minimization or proof
of semantic coverage. Keep original crash seeds, minimize copies, and replay both
with the same binary and instrumentation. A fixed seed alone does not reproduce
scheduling, mutable state or corpus changes.

Use matching LLVM source-based tools for source coverage and report its scope,
denominators, failures and profile compatibility separately from libFuzzer's
feedback counters. Verify coverage collection across normal and crashing exits.
Choose another engine only after qualifying its harness, build and reset
contracts. Do not infer efficacy, bug-discovery speed or agent superiority from
an installation check, known-seed replay or one favorable run.

See [qualified scope](references/qualification.md). Original instructions and
attribution are preserved in this overlay; coding-agent efficacy is unbenchmarked.
