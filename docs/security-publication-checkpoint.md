# Security publication checkpoint

This is an intermediate checkpoint for the ongoing catalog-wide work. It does
not establish improved model performance, complete all 673 skill reviews, or
claim that repository security is finished.

All 34 open Dependabot alerts in the 2026-10-07 snapshot map to locally resolved
versions or an absent dependency in the proposed locks. The crosscheck uses
Python packaging specifiers and npm's semver implementation against each exact
advisory range, including nested npm resolutions. GitHub closure remains
unverified until the updated default branch is published and analyzed.

The exact CI pip-audit invocation reports zero known findings in its 48-package
audit response. The explicit complete pinned inventory probe covers 52 packages
with zero known findings; the counts reflect different audit paths, not an
invented agreement. Seeded lock consistency also passes on Python 3.14.8. The
legacy environment's earlier checks ran on Python 3.12.14; they must not be
described as Python 3.14.8 results.

The qualified Python 3.14.8 environment passes 568 tests with two documented
NTFS/POSIX mode skips. Ruff, format and mypy pass. Catalog and overlay validation
pass. Tool and workflow version qualification remains distinct from hosted CI.

Credential neutralization policy 3 binds 34 complete canonical public source
resources to 66 replacement spans by file and substring SHA-256. Source values
are not stored in the registry. The source refresh verifies clean public Git
pins and reproduction of the previous mirrors before staging 24 affected skills
and linked metadata. It preserves other bytes, frontmatter, headings and line
counts. Encoded teaching samples remain syntactically base64 and use visibly
repetitive sample data. No provider was contacted to test example credentials.

The fresh unfiltered Gitleaks worktree snapshot decreases from 129 to 64
findings: all 65 targeted source-example locations are gone. The residual
locations concern two Key Vault version identifiers, one BuildKit file
reference, and 61 recorded evidence identifier/hash contexts. These remain in
the raw reports. The native Gitleaks command still exits 1, so its gate has not
passed. No path exemptions, finding baseline or suppression was added.

The independent curated worktree scanner reports zero findings and complete
coverage of tracked and nonignored untracked files. Historical scanning of the
original checkout still reports 22 provider-shaped teaching examples. A verified
all-ref Git bundle preserves the original refs; an isolated ignored checkout
holds a local history-cleanup preview. The working checkout and public main are
unchanged by that preview. Exact captured research evidence and original overlay
provenance retain transport-safe Git attributes. Resource-level research uses
the catalog's declared canonical hash policy so Windows CRLF and Git LF views
remain comparable; the original capture hashes and pre-migration ledger remain
archived. Other source changes still invalidate the resource review.

The provided AI identity rule requires `AI agent <>` for every AI-produced
history rewrite. The original default history contains 62 commits: 50 have that
AI identity, 12 map their author identity to the owner's real GitHub account,
and the initial commit uses GitHub's web-flow service as committer. The literal
human-identity rule therefore requires resolving that service committer before
publication. The local preview gives rewritten commits the required AI
identity. Original authorship mappings and messages must remain in the review
record; identity normalization is not evidence that the original human-labelled
work was produced by an AI.

Replacing public main with rewritten history requires a force-with-lease push
and changes commit IDs. No such push has been made. The public v0.2.0 tag, old PR
refs and GitHub-retained objects are separate historical surfaces; a default
branch rewrite must not be presented as erasing them. The six dependency PRs
remain open until their updates are reconciled with a verified published branch.
