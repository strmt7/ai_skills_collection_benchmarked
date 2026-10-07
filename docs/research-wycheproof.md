# Wycheproof review

The complete original single-file skill and all three resources at fetched
Trail of Bits `82fe8226252622fa807643bdca1710901198553a` were reviewed. The
newer skill changes its description and adds agent metadata and the vendor SVG;
the technical examples remain. This is a text/resource review, not a crypto
implementation audit, runtime benchmark pass or coding-agent comparison.

The current public Wycheproof repository is pinned at
`12fd3aaf33eb5fa1f52e026912ee00c054f9d984`. Its [README](https://github.com/C2SP/wycheproof/blob/12fd3aaf33eb5fa1f52e026912ee00c054f9d984/README.md)
documents a unified `testvectors_v1` directory and removal of language-specific
harnesses. The original skill's tree and reference-implementation promises are
outdated. The latest-release endpoint returns 404; do not invent a stable release
version for this continuously updated data repository. Pin reviewed commits,
file hashes, schemas and the adapter's supported parameter policy.

The selected AES-GCM file contains 316 tests in 45 groups: 229 valid and 87
invalid. Ed25519 has 151 tests in 78 groups: 88 valid and 63 invalid. Neither
selected file has acceptable cases. These are verified inventory counts, not
execution results. Both selected schemas, their complete five-file local
reference closure and AEAD vector notes were read. This is not executed schema
validation; custom byte/ASN/key formats and the adapter still need checks. A
mistyped legacy documentation URL returned 404 and is retained in the receipt.

The source's example harness can hide errors or misclassify results:

- The Python loader returns an empty list for a missing file, allowing pytest
  parametrization to perform no crypto checks. Fail closed and require selected,
  eligible, attempted and completed counts, plus declared/actual count agreement.
- IV filtering silently removes unsupported domains. Declare and justify provider
  constraints; retain every excluded ID and reason, and never call the subset a
  full-vector pass. Cases that the API cannot represent are different from bad
  authentication or implementation bugs.
- The decryption example refers to `InvalidTag` without importing it. Its handler
  also requires `ModifiedTag` on every such rejection, an assumption that must be
  checked against each algorithm's actual notes and failure reasons.
- Both Python directions treat acceptable cases like invalid cases. The JavaScript
  factory creates a test body for acceptable cases but makes no assertion.
  Explicitly implement each supported result/policy combination, including
  output correctness when an acceptable input is accepted. Unknown result values
  must fail adapter validation.
- Catching every JavaScript exception for an invalid signature turns unexpected
  type, API and internal failures into apparent correct rejection. Catch only
  documented rejection exceptions and preserve all unexpected failures.
- Encryption of an invalid authentication vector is not the same operation as
  rejecting its supplied ciphertext/tag. A complete adapter specifies operation,
  output and error expectations from the external algorithm/vector contract.
- Group metadata, key format, byte encoding, signature lengths and ID uniqueness
  must match the selected schema. A literal length of 128 is correct only for
  a particular hex representation of a 64-byte Ed25519 signature; it is not a
  generic EdDSA input contract or a complete signature validation repair.
- A Git submodule does not update automatically. Review updates into a new pin;
  never change vectors invisibly during a frozen comparison. Raw curl without
  HTTP failure handling or an atomic verified publication can cache an error
  response or partial JSON as an existing test file.

The currently observed stable Python `cryptography` release is 50.0.2. Its
[stable AESGCM API](https://cryptography.io/en/50.0.2/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)
defines nonce constraints and `InvalidTag`; the latest documentation endpoint is
51.0.0 development material. No dependency installation or actual provider-vector
execution is qualified by this review. Those checks, accepted-case controls,
schema closure, JavaScript adapters and independently evaluated coding tasks
remain required. Vector correctness does not test constant-time behavior or
prove the absence of cryptographic vulnerabilities.
