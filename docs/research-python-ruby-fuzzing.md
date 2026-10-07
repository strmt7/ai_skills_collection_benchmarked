# Python and Ruby fuzzing resource review

Read both complete original entrypoints at Trail of Bits commit
`e8cc5baf9329ccb491bfa200e82eacbac83b1ead`. At current skill-source commit
`82fe8226252622fa807643bdca1710901198553a`, read all five Atheris resources and
all three Ruzzy resources: entrypoints, Atheris examples/structured-input guide,
agent metadata and SVG assets. These are source reviews, not coding-agent scores.
The original mirrors remain unchanged. The resource comparison receipt records
raw and canonical hashes, added files and the declared normalization method.

## Release and platform qualification

Primary release metadata gives stable Atheris **3.1.0**, Ruzzy **0.8.0**, and
LLVM **23.1.2**. The current Atheris README advertises Python 3.11–3.14, while
the latest PyPI release provides only cp312/cp313/cp314 Linux x86-64 wheels.
Source support does not establish a wheel for every supported interpreter or
platform. Both original and current skill entrypoints still say Python 3.7+.
The Docker example defaults to 3.11/Clang 19 and a mutable base tag, and its
preload path hard-codes the Python 3.11 environment even if the build argument
changes. It does not qualify latest stable toolchain interoperability.

Current Ruzzy tool documentation additionally supports Apple Silicon macOS,
unlike the skill's Linux-only support description. It documents a non-system
Ruby, LLVM containing libFuzzer, `DYLD_INSERT_LIBRARIES`, appropriate bundle
linker flags, and problems with SIP-protected version-manager shims. Reading
those contracts does not qualify macOS installation here. Its development HEAD
documents structured input and an alternative LibAFL backend; those features
must be checked against the selected stable release before being promised.
The claim that Ruzzy is the only production-ready Ruby coverage fuzzer is
unqualified; tool suitability requires target/platform evidence.

## Eight actual Atheris controls

An owned offline image installs the complete, unchanged cp314 release wheel
after verifying its primary PyPI SHA-256. The image is pinned by its exact local
image ID and uses the qualified backend's original constraints: uid 65534,
network/IPC disabled, read-only root, capabilities dropped, bounded CPU/memory/
processes/output/time and inspected owned cleanup. No staging bound was relaxed.
The first proposed symbol-strip preparation failed because the base image lacks
`strip`; that failed receipt remains. The implemented image route performs no
wheel-content transformation. An explicit immutable-image parameter checks both
the requested and resolved local image IDs before candidate execution.

Actual Python 3.14.8/Atheris 3.1.0/urllib3 2.8.0 controls show:

- The original `atheris.__version__` verification raises `AttributeError`; use
  `importlib.metadata.version("atheris")` for distribution metadata.
- The original dynamic `dirname(atheris.__file__)` preload path misses the
  installed ASan library. `atheris.path()` resolves its actual directory. File
  existence alone does not qualify sanitizer initialization or target coverage.
- JSON decoding with `errors='ignore'` maps distinct valid/invalid byte inputs
  to the same parser input. Specify whether the contract is bytes or strict
  decoded text; intentional lossy normalization has a narrower tested domain.
- The HTTP example reads the entire wire message as body bytes, with status 0
  and empty headers. It does not parse request lines, response status or headers.
- The unchanged HTTP harness swallows an injected unexpected `RuntimeError`.
  This is an exception-policy control, not a native memory-corruption test.
- Actual structured providers return minimum/empty/false defaults for exhausted
  input. Count meaningful target calls and valid-domain coverage rather than
  equating throughput with target exploration.
- A genuinely instrumented pure-Python engine performs 64 bounded callbacks and
  exits successfully using `-atheris_runs=64`, with observed coverage events.
- The unchanged quick-start harness replays its known `FUZZ` seed and exits 77
  with the expected Python exception. This is replay, not independent discovery.

The first three harness receipts retain the adapter's failures: initially there
was insufficient assertion detail, then crash classification checked stderr
although this Atheris build prints its Python traceback to stdout. The corrected
receipt checks both streams and retains both. Engine warnings about unavailable
sanitizer helper functions remain visible; no native extension, ASan, UBSan or
leak-detection campaign is claimed. Coverage.py export remains unqualified.

## Harness and sanitizer policy

The JSON example imports its target outside `instrument_imports` and instruments
the wrapper only. That does not establish full target coverage. The new upstream
examples still contain the lossy decoder and body-only HTTP target; their note
incorrectly says both examples catch `Exception` broadly although JSON catches
only `ValueError`/`UnicodeDecodeError`. Structured-input advice is useful, but
stability of draws under mutation and surrogate exclusion depend on the target's
contract. Returning early on every short input can hide required empty-input
behavior. Exhaustion checks must follow independently specified preconditions.

Ruzzy's native example rescues all `Exception`; its pure-Ruby parser example
rescues all `StandardError`. Those can hide programming defects, and the former
also catches control-flow exceptions such as `Interrupt`/`SystemExit`. A campaign
deliberately restricted to native memory faults must state that narrower scope;
run independent semantic/error-contract checks instead of implying total safety.
These Ruby concerns are source findings, not executed Ruzzy controls.

Both skills inherit interpreter leak accommodations from tool guidance. Disabling
leak detection can be a documented interpreter accommodation, but it excludes
that vulnerability class from the campaign. Allocation exhaustion is not
universally low impact; service/resource contracts determine its consequence.
Record exclusions, reproduce relevant outcomes under explicit resource limits
and preserve a separate qualified native/leak test when that class matters.
Do not infer sanitizer coverage from compilation flags, preloading or a toy
crash alone. Verify target symbols, compatible runtime initialization and a
known instrumented target defect. Use disposable sources/corpora, bounded owned
artifacts, deterministic harnesses and reproducible minimized inputs.

The licensed Atheris and Ruzzy instruction overlays are experimental. Native
builds/toolchain compatibility, actual Ruzzy campaigns, macOS/ARM support,
coverage export and independent coding-agent comparisons remain required work.

Primary references:
[Atheris pinned tool README](https://github.com/google/atheris/tree/e36da74cf42b5834c4e31d7cabb58d796695d29f),
[native-extension guide](https://github.com/google/atheris/blob/e36da74cf42b5834c4e31d7cabb58d796695d29f/native_extension_fuzzing.md),
[Atheris release](https://pypi.org/project/atheris/3.1.0/),
[Ruzzy pinned tool README](https://github.com/trailofbits/ruzzy/blob/44bf09245e2612c8a97fee1be5573f8b2244784e/README.md),
[Ruzzy release](https://rubygems.org/gems/ruzzy/versions/0.8.0),
[LLVM release](https://github.com/llvm/llvm-project/releases/tag/llvmorg-23.1.2),
[Ruby exception hierarchy](https://docs.ruby-lang.org/en/master/Exception.html),
and [libFuzzer contracts](https://llvm.org/docs/LibFuzzer.html).

Evidence under `artifacts/research/2026-10-02/`:
`fuzzing-release-metadata.json`, `fuzzing-upstream-resource-comparison.json`,
`atheris-offline-image-preparation.json`, and
`atheris-harness-runtime-controls-v5.json`. Successful negative controls establish
specific defects; they are not runtime skill pass rates or agent gains.
