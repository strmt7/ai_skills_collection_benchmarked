# Qualification and limits

The 26 October 2026 Windows x64 checks used official LLVM 23.1.4 with
`-fsanitize=fuzzer,address`. The
[native controls](../../../../../benchmarks/component-controls/native-testing/source.json)
pin its archive and runtime identity. LLVM's versioned dictionary parser defines
accepted escapes independently of this overlay.

The mirrored PNG dictionary line, containing C-style `\r` and `\n`, failed with
`ParseDictionaryFile: error in line 1`. Its explicit hex-byte form loaded.
Separate controls admitted escaped quotes/backslashes and every byte value
from 0 through 255; an unterminated quote was rejected. The successful loads
establish parser acceptance, not mutation quality, decoded target reach,
long-running reliability or coverage improvement.

The runner retains native stdout, stderr, exits, input digests and process
cleanup receipts, including expected failures. AFL++, cargo-fuzz, go-fuzz,
automatic dictionary extraction and comparative campaigns were not run.
The original broad tool matrix therefore remains outside this qualification.

Primary references:

- [libFuzzer dictionary documentation](https://llvm.org/docs/LibFuzzer.html#dictionaries),
  read through the reviewed Crawl4AI provider.
- [LLVM 23.1.4 dictionary parser](https://github.com/llvm/llvm-project/blob/llvmorg-23.1.4/compiler-rt/lib/fuzzer/FuzzerUtil.cpp),
  captured as exact Git object bytes and verified against its Git blob digest.
- [W3C PNG signature](https://www.w3.org/TR/png-3/#5PNG-file-signature),
  read with the reviewed provider, independently specifies the eight input bytes.

This overlay remains unbenchmarked for coding-agent effectiveness. The failed
source example and repaired acceptance must not be reported as agent scores.
