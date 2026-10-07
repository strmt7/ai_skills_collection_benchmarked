# Qualification boundaries

Verified Linux x64 LLVM 23.1.3 native controls reproduce unchecked read failures
and long-path truncation returning success in the original replay example.
Empty inputs work under the tested glibc allocator, which does not prove portable
zero-sized allocation behavior. O3 source-based profiles export valid JSON;
lcov is a different format; repeated profile arguments select one profile rather
than a differential report. Merging two matching profiles preserves both target
paths (8 of 10 regions, versus 5 and 7 separately) in a fixed diagnostic fixture.
Those counts are not skill or agent improvement measurements.

Nine additional native controls qualify the supplied driver: complete valid,
empty, long-path and exact-limit replay, plus rejection of unreadable, oversized,
missing, symlink and directory inputs before target execution. Its fixed 1 MiB
bound is part of this qualification,
not a universal production input limit. Target, corpus and per-process runner
requirements still apply; the driver is not a sandbox or a complete coverage
collector. Crashing-profile durability, GCC/gcovr, other OS/architectures, profile
version migrations and coding-agent efficacy remain unqualified.

Sources: [LLVM stable release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.3),
[coverage mapping](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html),
[export formats](https://llvm.org/docs/CommandGuide/llvm-cov.html),
[profile merging](https://llvm.org/docs/CommandGuide/llvm-profdata.html).
Development documentation is context; actual stable runtime receipts establish
the narrower checked contracts.
