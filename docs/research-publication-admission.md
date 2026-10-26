# Exact mirror-byte admission

Mirror copying now applies the existing credential-shape and entropy detector
to the exact bytes selected for writing. This closes an admission gap in three
controlled cases: a dependency replacement, a binary carrier and a credential
assignment left after the declared neutralization. All three now reject before
writing and preserve an existing destination. Approved replacements remain
byte-exact; original upstream files and canonical hashing are unchanged.

The [mirror validator](../tools/check_mirror_content_admission.py) independently
checks current resources in CI, including binary and non-UTF-8 content. It rejects
external paths, empty catalogs and empty resource sets. The existing detector's
rules remain unchanged. Diagnostics report rule names and line numbers without
echoing matched values.

The [qualification record](../artifacts/research/2026-10-26/mirror-byte-admission-controls.json)
covers all 673 catalog entries: 17,671 resources, 235,295,126 bytes, including
414 binary or non-UTF-8 resources. All were accepted without modification.
The legacy credential-migration fixture now seeds its historical defect
directly, so the current publisher can refuse those old bytes while migration
still proves that it repairs them. No production guard is disabled for tests.

These are publication-policy and regression controls. They do not prove that
every possible secret is detected, close native scanner findings, or measure
coding-agent efficacy. Static review of the two owned clear-text findings
classified one fixed-fixture path as not actionable and left the generic copier
under review; both native findings remain visible. No rule exclusion, finding
dismissal or sanitizer rename was added. Existing historical secret matches
remain separate evidence. The actual original Kubernetes diagnostic helper also
completed its existing isolated command-spy controls after admission was added;
its known diagnostic defects remain recorded.
