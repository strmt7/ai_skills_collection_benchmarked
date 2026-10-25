# Agentic workflow auditor research

All 13 resources in the pinned Trail of Bits auditor package have now been
read. This completes the package-reading step, not its overall research or
runtime qualification. The original mirror remains unchanged. The
[review record](../artifacts/research/2026-10-25/agentic-workflow-auditor-review.json)
retains file-level bindings and limitations.

The current upstream package at
[`196a9073ab10d35bacf111f945e02c00b2c6883a`](https://github.com/trailofbits/skills/tree/196a9073ab10d35bacf111f945e02c00b2c6883a/plugins/agentic-actions-auditor/skills/agentic-actions-auditor)
still has 13 resources. Seven differ from the pin; all seven diffs were read.
They add legacy Claude input names, explain version-dependent list separators,
and improve cross-file secret tracing. Those claims still need checking against
the relevant action implementations before being treated as current defaults.

The package has useful data-flow guidance, but several findings remain:

- Its early exit for workflows without a directly recognized AI action precedes
  wrapper resolution. A wrapper-only integration can be missed. Resolution also
  stops after one level, so a clean result cannot establish arbitrary wrapper
  coverage.
- An example labeled safe inserts AI output directly into an inline shell
  script. Shell quoting does not isolate GitHub's earlier template expansion.
  This example remains in the current package.
- Permission allowlists, approval modes, operating-system sandboxes, caller
  admission and available credentials are separate boundaries. A permissive
  setting raises exposure; it does not by itself prove that an injection
  executed commands or accessed a secret. Claimed safe defaults require a
  version-specific check.
- Utilities such as `echo` do not intrinsically evaluate substitution syntax.
  The invoking shell, argument construction and tool permission parser determine
  whether interpretation occurs. Upstream proof claims are retained as claims;
  no attack payload was executed in this review.
- Wildcard actor settings must be assessed with the actual event, job gates and
  action authorization. A bot may relay attacker-controlled content; its account
  type alone does not establish that its text is trusted.

The new cross-file guidance explicitly tracks caller-provided inputs and secret
inheritance, including the need to inspect every resolved boundary. This improves
the method, but does not remove the one-level resolution limit or validate all
vendor-specific behavior.

The repository license is CC BY-SA 4.0; the pinned and current license files are
byte-identical. Any future adapted package must preserve attribution, indicate
changes and follow its applicable license conditions. This review creates no
adapted overlay. The earlier independently defined native workflow controls
remain frozen and do not measure coding-agent effectiveness or model superiority.
