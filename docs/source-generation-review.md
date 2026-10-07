# Source-generation portability and recovery

The existing portable tree digest encodes regular Git modes `100644` and
`100755`. Looking up the repository index repaired existing Windows mirrors,
but newly copied, untracked files still had no index entry and lost their
executable mode in NTFS file stats. Inferring executable status from filename
extensions would change the upstream contract and miss extensionless scripts.

New collection records therefore persist a complete relative `file_modes` map
from the source Git index. Catalog, mirror manifest, and source lock carry the
same map. Copying applies those modes where the filesystem supports them;
hashing uses the declared complete map on Windows and also checks actual
executable bits on POSIX. Missing, additional, or invalid mode entries reject
the tree. Legacy entries remain readable without inventing historical mode
metadata. Before Git publication, Windows index modes still need verification
against the recorded map; metadata cannot make NTFS represent execute bits.

Hashing and copying now share resource enumeration. Directory I/O errors and
unsupported nonregular file resources fail the build instead of silently
producing an incomplete tree. Existing nested-skill exclusions and deterministic
directory alias/cycle handling are retained.

Mirror publication first builds and verifies the full replacement in an ignored
workspace directory. Canonical destination paths, nonoverlap, source containment,
and source hashes are checked before replacing the current mirrors. The previous
tree is retained under `.venv/generation-staging/` for recovery. A failed copy or
changed input leaves it untouched; a failed publication rename attempts rollback.
The two directory renames are not an atomic multi-file transaction. An interrupted
process can require recovery from the retained stage/previous directory.

Focused tests exercise an extensionless executable, fresh untracked copies,
complete mode coverage, path escapes, source changes, copy failures, rename
rollback, empty-collection rejection and unreadable resource enumeration.
A full local Python 3.14.8 run passed 318 tests with two documented filesystem
skips. Current catalog validation, all 673 existing mirror hashes, offline source
lock checks and static-output freshness pass. No source refresh has been published.

## Whole-generator publication

The generator now collects inputs before writing any production output and stages
the complete declared catalog, mirror, entrypoint, selected manifest and documentation
set. Evaluator schemas remain independent, maintained scoring inputs and are never
rewritten by catalog generation. It validates required outputs and mirror hashes before replacing
anything. Source HEAD changes and uncommitted source changes reject collection.
Missing required output files cannot silently delete existing outputs. Undeclared
generated files also reject publication.

Publication retains each original under one recovery directory and records rename
operations in a journal. Injected failures during metadata, mirror, documentation
and journal publication restore the originals, including earlier replacements.
A failed rollback retains both available versions, an explicit failure record and
the publication lock. An existing lock is never removed speculatively. Recovery
directories are retained; retired output directories are moved there rather than
deleted. Canonical paths, links/reparse points, overlapping targets and changed
targets/staged inputs reject replacement. Unreadable directories do not hash as
empty trees. Unrelated sibling files and authored overlays are outside the declared
replacement set.

This remains a sequence of filesystem renames: concurrent readers can see an
intermediate state. A process interruption requires inspection of the retained
journal, original/replacement paths and lock before recovery. Power-loss durability
and hosted cross-platform execution have not been established.

`build_catalog.py` now exposes `build_parser()`, `main(argv)`, `--check` and `--json`.
Freshness mode stages and compares without publishing. Generated dates resolve
through the shared deterministic helper; `SOURCE_DATE_EPOCH` overrides the previous
manifest date, with a Git input timestamp fallback. README badges use the existing
badge renderer. The maintained installation guide is no longer overwritten by an
obsolete generated template. The final README rewrite remains a later work stage.

The complete fixture exercises actual generation, publication, repeated freshness,
drift, late failures and date precedence. The subsequent full suite passed 457 tests
with the same two documented NTFS mode skips; lint and type checks pass. See
`artifacts/research/2026-10-02/catalog-publication-controls.json`. Production mirrors
and source locks have not been refreshed by these tests.

Remaining generation work includes independent Git-index mode verification,
dependency-graph regeneration with recorded advisory transformations, upstream
rights/path review and hosted cross-platform execution.

The subsequent dependency review removed partial package-lock field rewriting.
Hashing/copying preserve complete graph content, including newer versions and
license metadata. Dedicated controls verify older, newer and prerelease graph
inputs without claiming that vulnerable inputs were repaired. All 673 current
mirror and offline source-lock hashes still pass. Historical transformations
belong to the historical generator snapshot; new graph qualification is explicit.

The later full Windows suite passed 478 tests with two NTFS mode skips. Thirteen
focused provisioner tests passed after separating original/staged input hashes
and moving dependency-graph checks before any copy. Lint/type checks remain green.

Actual Linux Docker controls now pass complete publication, repeated freshness,
later-rename rollback, symlink rejection and portable copy/executable-mode tamper
detection. They ran as UID 65534 in the qualified networkless/read-only-root
Python 3.14.8 image; temporary fixture and owned container cleanup were verified.
The first wrapper read the wrong response field and classified its successful
invocation as a failed control. That receipt remains; the corrected public wrapper
and `catalog-publication-linux-controls-v2.json` record the successful replay.
This is a focused POSIX contract qualification, not a full hosted/Linux CI pass.

The later credential-policy source loop publishes only affected source-locked
trees and their linked metadata, preserving the rest of the catalog and the
maintained README. Four clean public checkouts at the original locked commits
reproduce all seven old mirror hashes before deterministic neutralization.
Original/updated resource hashes, portable modes and source identities are
recorded in `artifacts/research/2026-10-02/credential-policy-refresh.json`.
The recoverable publisher retains every replaced tree and metadata file.
Sixteen migration/serialization controls pass, and live qualification checks the seven
refreshed originals. This does not upgrade upstream versions or remediate Git
history. See `docs/research-secret-scan-coverage.md` for the exact remaining scope.

## Scoped upstream release refresh (2026-10-07)

The later source loop advances `hugohe3/ppt-master` from v2.3.0 at
`19297c51cce3361d55137f527c010a8886f88bda` to the verified stable v6.6.0
release at `a50758ac29ec027e85966db33e2ae80031446756`. The other 672
skill mirrors retain their source signatures and contents. Legacy file-mode
maps are derived from the existing Git index and recorded explicitly in the
catalog and lock without changing their tree hashes.

The staged update exposed two generator defects: an outdated evaluator writer
would remove existing nonempty-string constraints, and a generic `workflow`
keyword would move the presentation skill into DevOps. Evaluators are now
excluded from catalog publication; this single-purpose presentation source has
an explicit reviewed category. All 673 skill IDs and all benchmark assignments
are preserved. Only its source-grounded provenance scenario changes with the
new source; those provenance records remain separate from runtime scores.

README inventory counts are read from existing repair and adapter manifests.
Generation preserves their documentation links and the complete offline quality
commands. A regression test verifies unchanged evaluator bytes, independent
artifact inventories and repeatable generation. Malformed inventory JSON aborts
publication before any catalog output is replaced. The full local Windows
suite after the source update passed 616 tests with two NTFS mode skips.
After fixing incomplete Windows Git listings and tracked-deletion handling,
the final full local suite passed 619 tests with two NTFS mode skips. The badge
writer now detects and normalizes CRLF byte drift; its check does not mutate the
README. Scoped regeneration reports no output drift. Ruff, formatting, mypy,
compilation, catalog, source-lock, static-artifact, risk-audit and curated
worktree secret checks also pass. These checks do not establish a native
Gitleaks history pass.

The recoverable source publication is local at this point. Its completion does
not establish full PPT rendering compatibility, all-source upstream freshness,
repository-wide security clearance or improved coding-agent effectiveness.

The subsequent hosted ledger gate exposed one transport defect: Git normalized
the captured Wycheproof input JSON, whose original CRLF bytes were bound into
research receipts. Its exact path now disables text conversion, preserving the
original input and expected hash. A regression check compares raw and filtered
Git object hashes for every ledger evidence path; it reproduced this mismatch
before the fix. No fixture value, evaluator or expected hash was changed.

Live source qualification also now enables long paths for every Git read and
rejects diagnostics even when Git exits successfully. This prevents unreadable
paths from being misreported as source edits. The selected PPT checkout passes
strict commit, tree, origin, clean-status and resource checks; the other 26
source repositories are outside this live qualification.
