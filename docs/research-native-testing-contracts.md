# Native memory checks and fuzzing dictionaries

Two experimental overlays correct observed compatibility problems in the
source instructions. Use them from an intact clone:

- [AddressSanitizer testing](../included/repaired/skills/address-sanitizer-current/SKILL.md)
  explains instrumented builds, platform limits and finite memory budgets.
- [Fuzzing dictionaries](../included/repaired/skills/fuzzing-dictionary-current/SKILL.md)
  explains byte-preserving token serialization and native dictionary checks.

Both retain Trail of Bits attribution, the complete CC-BY-SA-4.0 licence and
the unchanged original instructions. Follow the collection's
[mandatory agent tools](agent-tools.md) when using them.

| Source guidance | Verified finding or correction |
| --- | --- |
| Skip Windows/macOS ASan; describe Windows support as experimental | Current LLVM and Microsoft documentation supports native ASan on documented platforms. The Windows LLVM control detects an invalid access. MSVC and macOS were not executed here. |
| Disable libFuzzer RSS limits because ASan maps a large shadow address range | LLVM distinguishes virtual address mappings from resident memory. Keep a finite RSS budget; this review does not stress-test the limit. |
| Use `\r` and `\n` in a libFuzzer PNG dictionary entry | LLVM 23.1.4, 23.1.5 and 23.1.6 reject that line. Explicit `\x0D` and `\x0A` escapes load successfully. |
| Pass raw extracted strings directly into a dictionary | Extraction alone does not serialize embedded quotes, backslashes or binary bytes. Separate native controls admit escaped strings and all 256 byte values. |

The native run has **11 successful controls**, including compiler identity,
compilation, a clean ASan run, an expected ASan failure, fuzzer help, three
accepted dictionaries and two expected dictionary failures. Every child runs
inside an owned Windows process tree with a deadline and bounded logs. Expected
failures remain in the evidence; they are not converted into clean runs.

The current qualified compiler is the official **LLVM 23.1.6 Windows x64**
portable archive, observed on 17 November 2026. The
[17 November update](../artifacts/research/2026-11-17/llvm-toolchain-refresh/review.json)
retains its verified asset identities, all 11 native outcomes and the original
266-character SDK DLL startup failure. The
[10 November record](../artifacts/research/2026-11-10/llvm-toolchain-refresh/review.json)
retains the earlier 23.1.4 and 23.1.5 evidence.

The runner deploys its digest-verified matching ASan DLL beside the owned test
executables. This Windows app-local deployment supports the longer SDK DLL path;
it does not establish arbitrary executable-path support or change global PATH
or registry settings. Executable paths retain their documented loader limits.
Windows builds currently require installed MSVC C++ headers/libraries and a
Windows SDK. The runner discovers them and records selected paths in the verbose
build log; qualification did not install or modify them. Fresh automatic setup
of those prerequisites remains unqualified. Tool paths come from explicit inputs
and discovery, without a fixed username or drive.

These controls prove specific native contracts. They do not measure a fuzzing
campaign's coverage or bug yield, validate every tool mentioned by the original
skills, or show an advantage over a default coding agent. Both overlays remain
unbenchmarked for agent effectiveness. Research, revision and evaluation stay
open in the per-skill ledger until their remaining scope is qualified.

The current upstream skill bodies still contain the reviewed issues: the
checked newer commit changes their activation descriptions only. The locked
mirrors were not edited or advanced as part of this repair loop.

Primary evidence includes [LLVM ASan](https://clang.llvm.org/docs/AddressSanitizer.html),
[MSVC ASan](https://learn.microsoft.com/en-us/cpp/sanitizers/asan?view=msvc-170),
[libFuzzer](https://llvm.org/docs/LibFuzzer.html) and the
[PNG signature specification](https://www.w3.org/TR/png-3/#5PNG-file-signature),
read with the reviewed isolated Crawl4AI provider. Exact LLVM and Trail of Bits
Git objects were captured through the native API and checked against their
blob identities. The [research record](../artifacts/research/native-testing/review.json)
contains source, licence, capture and outcome digests.

## Reproduce the native checks

With CPython 3.14 and the required Windows build components, run from the clone:

```powershell
$taskNativeRoot = Join-Path (Get-Location) '.venv/native-testing'
New-Item -ItemType Directory -Path $taskNativeRoot
$spec = Get-Content benchmarks/component-controls/native-testing/source.json -Raw | ConvertFrom-Json
Invoke-WebRequest -Uri $spec.archive_url -OutFile (Join-Path $taskNativeRoot 'llvm.tar.zst') -TimeoutSec 180
python -I benchmarks/component-controls/native-testing/run_native.py --archive (Join-Path $taskNativeRoot 'llvm.tar.zst') --toolchain (Join-Path $taskNativeRoot 'toolchain') --workspace (Join-Path $taskNativeRoot 'workspace') --output (Join-Path $taskNativeRoot 'observations')
```

The archive's exact size and SHA-256 are checked before extraction. Extraction
uses a bounded decoder and rejects links, escaping paths and excessive expanded
size. Use new directories for another run; failures and existing results are
never replaced. A previously extracted matching compiler can be selected with
`--compiler` instead of `--archive` and `--toolchain`.

The [Windows workflow](../.github/workflows/native-fuzzing-controls.yml) reruns
the controls and retains actual logs. It fails when a newer stable LLVM release
requires requalification. Offline CI separately checks published evidence
against its current fixtures and collector. Contributor validation is described
in [the development guide](../CONTRIBUTING.md).
