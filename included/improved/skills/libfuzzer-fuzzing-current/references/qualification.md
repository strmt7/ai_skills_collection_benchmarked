# Qualification boundaries

Twelve native source-contract controls use verified Linux x64 LLVM 23.1.3 and
Python 3.14.8. The compiler, profile tools and runtimes come from a digest-verified
official release subset; fixed examples compile offline with the matching linker
in a separately pinned build image. Immutable binaries then run under the original
read-only, networkless, unprivileged, bounded backend, retaining noexec temporary
storage and verified cleanup.

Known zero-denominator replay faults at O0; the unused original operation is
eliminated at O2. A defined-byte-decoding, observable-result fixture reports the
known division through explicit UBSan and accepts a valid denominator. Native
source-based coverage and replay/export/profile controls qualify the associated
coverage contracts. These are source-grounded controls, not independently scored
skill tasks, bug-discovery campaigns or agent trials. Leak detection is explicitly
disabled in the sanitizer smoke; leak safety is not qualified.

Failures are retained: initial images lacked a linker/development environment,
and the first runtime classifier expected different wording for a real FPE report.
The classifier now checks the observed specific fault, without changing the
target, expected defect or execution constraints. Other platforms, dependencies,
engine migrations, long campaigns and coding-agent gains remain unqualified.

Primary sources: [LLVM 23.1.3](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.3),
[stable flag definitions](https://github.com/llvm/llvm-project/blob/0d261d1ca552c95a8f007e061c787ac7132fbcbc/compiler-rt/lib/fuzzer/FuzzerFlags.def),
[provider contract](https://github.com/llvm/llvm-project/blob/0d261d1ca552c95a8f007e061c787ac7132fbcbc/compiler-rt/include/fuzzer/FuzzedDataProvider.h).
