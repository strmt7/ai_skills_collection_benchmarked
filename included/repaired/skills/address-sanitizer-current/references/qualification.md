# Qualification and limits

The 26 October 2026 Windows x64 checks used the official LLVM 23.1.4 portable
archive. Its archive, compiler and ASan runtime digests are pinned in the
[native controls](../../../../../benchmarks/component-controls/native-testing/source.json).
The Windows build also needs installed MSVC C++ headers/libraries and a Windows
SDK. The runner lets LLVM discover them through the system's standard program
locations; it neither bundles nor changes those installations. Their selected
paths and versions appear in the verbose native build log.
A valid array access exited successfully; the matched out-of-bounds access
produced `AddressSanitizer: heap-buffer-overflow` and a nonzero exit.
This proves the selected fixture's detection, not a whole application's
instrumentation. MSVC, macOS, GCC, leak checks, Rust and AFL++ were not executed
in this qualification.

The first private extraction hit CPython's default Zstandard window limit.
Recovery kept the verified archive and used an explicit 1 GiB decoder-window
bound. The first clean executable then failed at Windows loader startup with
`0xC0000135`: its matching ASan DLL was outside the process search path.
Adding that archive's runtime directory to only the test process's `PATH`
restored startup. Both failures remain separate from sanitizer diagnostics.
The first restricted-environment run also omitted Windows program-location
variables, preventing SDK discovery. Its compiler error is preserved; the
runner now passes only those discovery variables and essential process paths,
without inheriting compiler overrides, credentials or other project settings.

The published runner uses owned Windows process trees, deadlines and bounded
logs, and retains actual native outcomes. The fuzzer controls use finite RSS,
per-allocation and input budgets. They do not stress-test the RSS limit or
certify every possible resource-exhaustion case.

Primary references, captured through the reviewed Crawl4AI provider:

- [LLVM AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html):
  supported platforms, memory mappings and platform-specific leak checks.
- [MSVC AddressSanitizer](https://learn.microsoft.com/en-us/cpp/sanitizers/asan?view=msvc-170):
  Windows support, compiler switches and incompatible options.
- [libFuzzer](https://llvm.org/docs/LibFuzzer.html): RSS and allocation limits,
  periodic checking and in-process leak detection.

These are component contracts. This overlay remains unbenchmarked for
coding-agent effectiveness; it has no demonstrated advantage over a baseline.
