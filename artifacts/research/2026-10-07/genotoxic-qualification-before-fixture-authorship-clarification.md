# Qualification

The [28 runtime and source-example controls](../../../../../artifacts/research/2026-10-07/mutation-tool-runtime-controls.json)
use Python 3.14.8, mutmut 3.8.0 and Trailmark 0.5.0. The provider resolves
tree-sitter 0.25.2 and tree-sitter-language-pack 1.21.0 under Trailmark's declared
constraints. A separately hashed release bundle supplies only its Python
grammar. The isolated executions use no network, a read-only root, nonroot UID,
no capabilities and bounded CPU, memory, PIDs, output and scratch space. The
mutation profile adds a private 16 MiB `/dev/shm` tmpfs while retaining IPC mode
`none`; inspection rejects host IPC or an unbounded/different filesystem.

The threshold fixture generated six identical mutant IDs in both campaigns.
Weak tests left one survivor and five untested mutants. Adding boundary tests
killed that survivor while the same five remained untested. This is a controlled
tool integration demonstration; an AI agent did not generate the tests.

The real graph fixture resolves an internal call and an externally invoked
function with zero local callers. Executed original source functions dismiss
that function and an unmapped case as false positives, choose ambiguous names
by insertion order, exclude `src/contest.py`, and associate a removal with only
the first of two mutants. These are source-example reproductions, not skill
runtime benchmark passes. Forged totals and unverified cleanup fail controls.

Both original package texts were completely read. Current upstream delta
review confirms improved tool installation and reachability queries; it does
not remove the reproduced mapping/accounting issues. Other language tools,
cross-module graph completeness, Necessist runtime and production campaigns
remain unqualified here. The overlay is efficacy-unbenchmarked.

Primary contracts: [mutmut released README](https://github.com/boxed/mutmut/blob/14a7230049a5c8abd90c2bb0f7438e30da6471f5/README.rst),
[Trailmark released query API](https://github.com/trailofbits/trailmark/blob/6ee0f2252d7d5ceed31210491332a553c1af4b23/src/trailmark/query/api.py),
[parser cache/download implementation](https://github.com/xberg-io/tree-sitter-language-pack/blob/09a36885b33ab6e4b010cf04acbb9876ddfb52cc/crates/ts-pack-core/src/download.rs).
