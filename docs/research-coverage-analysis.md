# Coverage-analysis review

The complete original single-file package and all three resources at fetched
Trail of Bits commit `82fe8226252622fa807643bdca1710901198553a` were reviewed.
The newer skill changes its description and switches gcovr installation to uv;
the replay runtime, reporting and comparison examples otherwise remain. Agent
metadata and the vendor SVG were added. This is a text/resource review, not a
coverage campaign, runtime-readiness pass or coding-agent comparison.

Freeze the program revision, harness, instrumented modules, build flags,
toolchain, corpus and reset rules before comparing coverage. Report relevant
regions/branches reached and their denominators, parser progress and failures.
Coverage shows execution; it does not establish a correct oracle, exploitable
bug discovery or superior agent behavior. The original advice to skip analysis
whenever crashes are still being found can hide untested code. Increased coverage
does not automatically justify a larger corpus; minimization and input semantics
still matter. A decrease after a source change can reflect changed denominators.

The original C/C++ corpus runtime uses a fixed path buffer and unchecked seek/tell
results, assumes `dirent.d_type` identifies every regular file, reads arbitrary
file sizes, and reports individual read/allocation errors while returning overall
success. It neither counts attempted/successful inputs nor sorts traversal or
resets target state. The empty-input contract depends on zero-sized allocation
behavior. A reliable replay must reject incomplete collection and preserve the
target's valid byte domain; optional directory-entry type information cannot
define which files were tested. Subsequent native controls reproduce unreadable
inputs and long-path truncation returning success. Empty replay works under the
qualified glibc allocator; this is not portable malloc(0) proof.
The portable contracts are specified by POSIX
[readdir](https://pubs.opengroup.org/onlinepubs/9799919799/functions/readdir.html)
and [malloc](https://pubs.opengroup.org/onlinepubs/9799919799/functions/malloc.html).

Forking each input does not by itself preserve crash coverage. The example
ignores fork/wait status and inherits a common profile filename. Use bounded
subprocesses, explicit outcomes and qualified profile paths/merging rather than
dropping crashing inputs from the denominator. LLVM documents process-specific
profile paths, runtime merge patterns, crash-recovery limitations and raw-format
compatibility in [source-based coverage](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html).
That guide also contradicts the blanket claim that LLVM source-based coverage
becomes misleading at O3: source-region mappings precede optimization. Separate
LLVM source-based, GCC gcov and fuzzer feedback instrumentation and record the
actual build used. Compiler optimization can still change program behavior and
must remain controlled between experimental conditions.

Several examples need correction:

- An lcov export redirected to `coverage.json` is not JSON. The shown abbreviated
  export and directory-report commands also omit their binary/profile inputs.
- Repeating `-instr-profile` in one `llvm-cov show` command does not define a
  differential comparison. Export each matching binary/profile separately, then
  compare explicit file/region identities and denominators.
- The GCC example forces `llvm-cov gcov`; this is not a generally supported
  substitute for the matching GCC gcov executable. LLVM documents compatibility
  with GCC 4.2 and only possible compatibility with later versions.
- The CMake example requests 3.0 policy compatibility. CMake 4 removed
  compatibility below 3.5; update and qualify the project's policy range.
- Broad substring filename exclusions can hide unrelated target files. Freeze
  an explicit instrumented-file scope and report every exclusion.
- Ignoring gcov parsing errors must produce an incomplete result, not a claimed
  complete or passing benchmark.

The output formats and command inputs are documented in
[llvm-cov](https://llvm.org/docs/CommandGuide/llvm-cov.html), profile merging in
[llvm-profdata](https://llvm.org/docs/CommandGuide/llvm-profdata.html), and parser
compatibility in [gcovr](https://gcovr.com/en/stable/guide/gcov_parser.html).
CMake's policy break is recorded in its [4.0 release notes](https://cmake.org/cmake/help/latest/release/4.0.html).
Primary registry observations give gcovr 8.6 and CMake 4.4.3; neither was installed
or runtime-qualified in this review. The current LLVM documentation includes
development material. On October 7, verified stable LLVM 23.1.3 compiler,
linker, sanitizer smoke and profile tools are qualified by native receipts.
All 21 controls pass under the original runtime isolation constraints. O3
source-based profiles export valid JSON; lcov does not. Repeated profile options
select one profile, while proper merging preserves both selected target paths.
Nine controls qualify the overlay's bounded single-file replay driver. They are
source-contract checks, not coding-agent comparisons or independent skill scores.

Remaining work: independently evaluate the explicit coverage overlay on realistic
development tasks and qualify crashing-profile durability, other platforms,
GCC/gcovr and full collector accounting. Keep originals, real failures,
crashing-input accounting and sealed holdouts intact.
