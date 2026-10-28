# Azure Key Vault Java: safer examples

The [Key Vault Java security overlay](../included/repaired/skills/azure-keyvault-java-security/SKILL.md)
is an opt-in repair of the locked skill. Twelve tested examples no longer print
secret values or prefixes, and 14 literal secret-value arguments are labeled as
placeholders. Obtain real values through an approved secure input; do not commit
or log them.

Use the overlay within this checkout so its linked agent-tool policy and
supporting files are available. The original skill text and the upstream MIT
license are retained in the overlay's `provenance/` directory. The
[`repair.json`](../included/repaired/skills/azure-keyvault-java-security/repair.json)
records its source and file hashes. Verify it with:

```sh
python tools/check_keyvault_security_overlay.py --check --json
```

The [security control](../artifacts/research/2026-10-28/azure-keyvault-output-security-control.json)
records 12 original examples that emitted a synthetic value or prefix when
compiled with local fake SDK objects. The repaired snippets were tested under
the same conditions. Those controls do not use Azure or real secrets, and do not
establish complete skill security or an agent-performance improvement.

The original mirror remains unchanged and can still print values if its
examples are copied as-is. Microsoft's [security guidance on logging](https://learn.microsoft.com/en-us/azure/well-architected/security/monitor-threats)
and [secrets guidance](https://learn.microsoft.com/en-us/azure/security/fundamentals/secrets-best-practices)
explain why secret values should not be logged or hardcoded.
