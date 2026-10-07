# Dependency remediation checkpoint

The 2026-10-07 GitHub snapshot contains 34 open Dependabot alerts and six open
dependency PRs. These are hosted observations; a local repair does not close an
alert until GitHub analyzes the published default branch. No alert was dismissed
or suppressed, and no PR was closed during preparation.

The hashed Python lock resolves urllib3 2.8.0, msgpack 1.2.3 and idna 3.20. Their
current stable releases were checked against PyPI. The complete pinned graph has
no known findings in the fresh pip-audit run, and seeded pip-tools consistency
passes without changing the lock. This is one Windows/Python 3.14.8 resolver
environment; CI audits the graph on Linux and verifies consistency on Windows.

The original OpenDirectory image package remains pinned at public commit
`bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4`. Its existing mirror had historically
patched individual lock entries, an approach removed from the generator. The new
declared advisory policy raises only the affected direct Sharp declaration to
`^0.35.5`, retaining the other eight original direct dependency ranges and all
nondependency source resources. npm 12.2.0/Node 26.10.0 resolves and installs the
complete replacement graph. The npm advisory response reports zero findings
across 125 dependency records, including optional platform packages.

Resolved packages include Sharp 0.35.5, fast-uri 3.1.8, protobufjs 7.6.6,
`@protobufjs/utf8` 1.1.2 and ws 8.22.0. Brace-expansion is absent from the new
graph. Latest major releases of transitive libraries are not forced into
incompatible parent dependency ranges. Deprecated package warnings remain
visible. Advisory absence does not prove absence of undiscovered vulnerabilities.

`data/dependency_graphs.json` binds the exact upstream declaration/lock hashes,
the original complete source tree, the previous mirror tree, and the complete
qualified replacement pair. `tools/refresh_dependency_graph.py` verifies the
clean public checkout, stages the pair and linked catalog/manifest/source-lock
metadata, and publishes through the recoverable catalog publisher. Ordinary
file hashing still preserves input graphs. Source generation and live source
validation apply only the explicit policy for the exact original public pin;
unqualified newer upstream commits do not inherit it automatically.

The old mirrored declaration, lock and ISC license are preserved under
`artifacts/research/2026-10-07/image-cli-previous-mirror-graph/`. Publication retains
the original tree and metadata in an ignored recovery directory. A failed first
live replay records an HTTPS origin spelling mismatch; the corrected replay
checks all 28 locked OpenDirectory skills with no errors. Both receipts remain.

Nine trusted image/CLI controls pass against the new installed graph, including
image conversion, SDK response parsing and CLI imports. Two negative controls
continue to reproduce the existing short-key masking and false-success defects.
Dependency remediation does not repair those implementation defects, validate
paid-provider availability, or establish improved coding-agent performance.

The release workflow already selects immutable softprops/action-gh-release
3.0.3 rather than the older bot PR's 3.0.2. All bot diffs must be reconciled with
the published checkpoint before superseded PRs are closed. Historical credential
findings and fresh whole-worktree Gitleaks verification remain separate pre-push
work; this checkpoint is not a claim that repository security is complete.
