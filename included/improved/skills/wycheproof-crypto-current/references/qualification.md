# Qualified scope

The collection's `wycheproof-provider-runtime-controls-v2.json` records actual
offline execution against cryptography 50.0.2, OpenSSL 4.0.3 and Python 3.14.8:
283 eligible AES-GCM cases and all 151 Ed25519 cases pass. All 316 AES-GCM IDs
are accounted for; 33 cases are excluded by the declared 8..128-byte nonce API
domain. Both selected files lack acceptable results. Acceptable-result policy
checks are synthetic, not extra public-vector passes.

Twenty-one controls qualify offline Draft 7 schema/reference closure, custom
formats, count/ID/result validation, key representation agreement, provider
exception handling and two reproduced original example defects. They are
integration/provenance controls, not a skill-versus-default agent benchmark.
The first 18-control run and its exact source files remain separately archived.

The provider image installs eight hash-qualified stable wheels offline and
passes `pip check`. Execution uses the inspected read-only, network-disabled,
non-root bounded backend. These constraints are execution controls, not a claim
of cryptographic completeness or container-escape certification.

Primary contracts used for these decisions:

- [Pinned C2SP Wycheproof repository](https://github.com/C2SP/wycheproof/tree/12fd3aaf33eb5fa1f52e026912ee00c054f9d984)
  and its schemas/algorithm notes. Test vectors are Apache-2.0 licensed and fetched
  separately; they are not embedded in this overlay.
- [cryptography 50.0.2 AESGCM](https://cryptography.io/en/50.0.2/hazmat/primitives/aead/#cryptography.hazmat.primitives.ciphers.aead.AESGCM)
  and [Ed25519](https://cryptography.io/en/50.0.2/hazmat/primitives/asymmetric/ed25519/).
- [jsonschema validation](https://python-jsonschema.readthedocs.io/en/stable/validate/)
  and [referencing registry controls](https://referencing.readthedocs.io/en/stable/).

Other algorithms, providers, operations and JavaScript adapters are not runtime
qualified by these receipts. Constant-time behavior and coding-agent efficacy
remain unmeasured. Requalify versions and API constraints when adapting this
guidance to another project.
