---
name: address-sanitizer-current
description: Build and qualify AddressSanitizer checks for native memory errors in C/C++ tests or fuzz targets. Use for instrumented builds, runtime diagnostics and crash replay, with explicit platform and memory-budget limits.
license: CC-BY-SA-4.0
metadata:
  status: experimental-unbenchmarked
---

# AddressSanitizer testing

Follow the collection's [mandatory agent tools](../../../../docs/agent-tools.md).
Use ASan in a test build. Its runtime is not a production hardening mechanism.
Identify the actual compiler, target architecture, runtime and code under test;
support and available checks differ between implementations.

For Clang, compile the target sources with `-fsanitize=address -g -O1
-fno-omit-frame-pointer` and link through the same compiler driver with ASan
enabled. For a libFuzzer target, `-fsanitize=fuzzer,address` also supplies the
fuzzer driver; use `fuzzer-no-link` when another target supplies that driver.
Do not assume instrumenting a wrapper instruments a prebuilt dependency.

Windows and macOS can run ASan. LLVM and MSVC have different platform and
feature limits. MSVC supports `/fsanitize=address` on Windows 10 and later for
x86/x64; remove incompatible `/RTC`, edit-and-continue and incremental linking
options. A standalone LLVM Windows build may require its matching ASan DLL
directory on the test process's `PATH`. Keep that change local to the test;
do not replace system runtimes. See the exact tested scope in
[qualification](references/qualification.md).

Prove startup and detection with a small known invalid access and a matched
valid control before running the real suite. Preserve the diagnostic and
nonzero exit of the invalid control. Verbose startup output alone does not
prove target instrumentation or memory-error detection. Verify that reports
resolve to the tested source; record any missing symbols or uninstrumented code.

Keep virtual address mappings separate from resident memory. ASan's large
shadow address range does not justify `-rss_limit_mb=0`. Give libFuzzer a
finite RSS limit, per-allocation limit, input timeout, maximum input length and
campaign budget appropriate to the host. Its RSS checks are periodic and do
not replace an external process/resource boundary. AFL++ address-space limits
are a separate mechanism; qualify its sanitizer-specific setup before use.

Enable only the runtime options needed for the experiment. Preserve leak
reports when leak checking is in scope. LeakSanitizer availability is platform
specific: LLVM documents default Linux detection and optional macOS detection;
Windows ASan qualification here establishes no leak detection. Disabling leaks
changes the tested scope and must be recorded. In-process libFuzzer can report
supported leaks before normal shutdown; do not discard them as output clutter.

Retain exact compiler/runtime identities, build flags, target and fixture hashes,
bounded process logs, crash inputs and replay outcomes. A clean run means only
that these exercised paths produced no ASan diagnostic. It is not a proof of
memory safety, all sanitizer classes, or better coding-agent performance.

Adapted from Trail of Bits under CC-BY-SA-4.0. See [attribution](NOTICE.md),
the complete [licence](LICENSE) and the preserved original under `provenance/`.
