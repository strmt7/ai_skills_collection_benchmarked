# libFuzzer review

The original single-file package and the complete three-resource upstream package
at Trail of Bits `82fe8226252622fa807643bdca1710901198553a` were read. A fresh
October 7 remote check still reports that upstream head. The newer package changes
its activation description and adds agent metadata and a vendor SVG; its technical
examples otherwise remain. This review does not establish skill or agent efficacy.

LLVM reports libFuzzer as supported for important bug fixes, with no expectation
of major new features. Choose it for a suitable in-process target after checking
platform, compiler, sanitizer and campaign requirements. The original blanket
claims about ease, future maintenance and switching fuzzers are not measured
comparisons. An exported entrypoint alone does not qualify another engine's build,
persistent-state, instrumentation or execution contracts.

The raw integer-pointer casts in the examples assume suitable alignment, object
access and host byte order. Decode an explicitly defined byte order or use a
qualified provider rather than adding harness undefined behavior. Preserve valid
empty/malformed inputs; size rejection needs a target-specific reason. The division
example discards its result, allowing optimization to remove the operation. An
observable result and a sanitizer capable of detecting the intended defect need
qualification against a known input before a campaign can support any finding.

The FuzzedDataProvider example is **not** an empty-vector indexing defect:
`ConsumeBytesWithTerminator` always appends a terminator, and its official header
includes the standard vector and allocation declarations. The unexplained `0xFF`
terminator, lengths including that byte, arbitrary allocation size and `free`
ownership still need to match the actual `concat` contract. Do not infer a defect
without inspecting that target. Provider behavior is pinned in the
[23.1.3 header](https://github.com/llvm/llvm-project/blob/0d261d1ca552c95a8f007e061c787ac7132fbcbc/compiler-rt/include/fuzzer/FuzzedDataProvider.h).

Several operating instructions need qualification or replacement:

- The example LLVM 18 installation and libpng 1.6.37 download are historical,
  not current stable dependency recommendations. Verify a supported release,
  checksum and compatibility before building; preserve reproducible old inputs
  only when they are explicitly the experiment's subject.
- LLVM's `-rss_limit_mb` limits resident memory, not ASan's reserved shadow
  address space. Disabling it does not fix an address-space limit and removes a
  useful campaign bound. The shown `ASAN_OPTIONS=rss_limit_mb=0` and `stack_size`
  are absent from the stable common sanitizer flag definitions. Verify actual
  runtime help and distinguish resource limits, allocation failures and crashes.
- Nonfatal ASan recovery is not a general performance repair. Retain trustworthy
  failure boundaries and do not disable fortification, leaks or error reporting
  merely to get a passing run. Any exclusion needs an explicit measured scope.
- `-jobs` is the total number of campaigns; `-workers` is their concurrency.
  Nesting jobs/workers with fork mode multiplies processes and complicates
  limits. Qualify one orchestration mode and the total resource budget.
- A fixed random seed alone cannot reproduce scheduling, target nondeterminism,
  changing corpora, compiler behavior or environmental state. Preserve binaries,
  hashes, flags, corpus order, reset rules and replay outcomes.
- Greedy header extraction or raw `strings` output is not a validated dictionary.
  Quote/escape accepted entries, bound size and test the dictionary parser before
  attributing any coverage or throughput change to it.
- Corpus feature minimization and individual crash-input minimization are
  different operations. Keep crash artifacts and logs separately; minimized
  feedback features do not prove semantic equivalence or exhaustive coverage.
- CMake 3.0 policy compatibility is incompatible with current CMake 4; establish
  an appropriate project policy range and qualify the actual build.

Stable flag definitions are recorded in
[FuzzerFlags.def](https://github.com/llvm/llvm-project/blob/0d261d1ca552c95a8f007e061c787ac7132fbcbc/compiler-rt/lib/fuzzer/FuzzerFlags.def)
and [sanitizer_flags.inc](https://github.com/llvm/llvm-project/blob/0d261d1ca552c95a8f007e061c787ac7132fbcbc/compiler-rt/lib/sanitizer_common/sanitizer_flags.inc).
The public [libFuzzer guide](https://llvm.org/docs/LibFuzzer.html) is useful context,
but includes development documentation and is not a stable-runtime certificate.

LLVM 23.1.2 image preparation failed because the selected dependency subset
and execution base lacked a linker/development environment. Failures are retained.
On October 7, the primary release
endpoint reports stable LLVM 23.1.3; its Linux x64 asset was downloaded and verified
against its exact published size and SHA-256. A corrected offline fixture image
now builds with the matching linker in a separately pinned development stage.
Twelve source-contract controls pass in the original isolated execution profile;
nine more qualify the explicit bounded coverage replay driver. The original
division faults at O0 but is eliminated at O2; the checked fixture reports its
known zero denominator and accepts a valid denominator. The original replay can
fail to read an input and still report success. Profile/format/merge controls are
recorded separately in immutable receipts. Leak detection is disabled for the
sanitizer smoke. These are known-input controls, not a sanitizer campaign,
independent skill benchmark, coding-agent score or superiority evidence.
