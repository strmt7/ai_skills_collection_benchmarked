---
name: fuzzing-dictionary-current
description: Create and validate byte-correct fuzzing dictionaries for parsers, protocols and structured formats. Use when a coverage-guided fuzzer needs meaningful tokens, with native syntax checks and controlled campaign comparisons.
license: CC-BY-SA-4.0
metadata:
  status: experimental-unbenchmarked
---

# Fuzzing dictionaries

Follow the collection's [mandatory agent tools](../../../../docs/agent-tools.md).
Derive tokens from the target's independently specified input format and actual
parser comparisons. Keep the input encoding explicit. Dictionaries guide
mutations; they do not enforce a grammar, replace structured seeds or guarantee
coverage gains. Treat generated suggestions as candidates requiring validation.

For libFuzzer, use one quoted token per line, optionally with `name=` before
the opening quote. Blank lines and lines beginning with `#` are comments.
Escape quotes with `\"`, backslashes with `\\`, and arbitrary bytes with
exactly two hexadecimal digits after `\x`. C escapes such as `\r`, `\n` and
`\0` are not supported by the qualified libFuzzer dictionary parser.

For example, the PNG signature is represented as:

```text
png_magic="\x89PNG\x0D\x0A\x1A\x0A"
```

Validate the complete file with the actual selected fuzzer and retain its
diagnostics before starting a campaign. The original mirror's PNG line is
rejected by LLVM 23.1.4 because it uses `\r` and `\n`; the explicit byte form
above loads successfully. See [qualification](references/qualification.md).
Recheck other fuzzers' accepted syntax and version-specific limits separately.

Do not pipe raw `strings` output or greedy quoted-source matches directly into
a dictionary. Those operations do not escape embedded quotes, backslashes or
binary values, and C source literals may need decoding or concatenation first.
Extract candidate byte sequences, deduplicate by decoded bytes, serialize with
the selected fuzzer's supported escapes, then validate the result. Never execute
an extracted string. Preserve non-ASCII and NUL bytes according to the target
contract; base64 text is a different input unless the target expects base64.

Use `-dict=path` for libFuzzer. Choose input-length and dictionary-entry bounds
from the target and fuzzer implementation. Do not prescribe a universal optimal
token count. Confirm AFL++ `-x`, automatic dictionaries and Rust/Go harness
integration against their actual installed versions before using those modes;
libFuzzer qualification does not certify them.

Evaluate usefulness with the same target build, instrumentation, seed corpus,
resource budget and independent coverage collector, using separate output
directories. Repeat paired campaigns with predeclared seeds and alternating
order; report target coverage, valid-input reach and reproducible unique bugs,
alongside execution counts and cost. Retain neutral and negative results.
Parsing successfully or replaying a supplied crash proves neither discovery
rate nor a coding-agent advantage. Any agent comparison needs separate held-out
tasks and evaluators defined independently of these instructions.

Adapted from Trail of Bits under CC-BY-SA-4.0. See [attribution](NOTICE.md),
the complete [licence](LICENSE) and the preserved original under `provenance/`.
