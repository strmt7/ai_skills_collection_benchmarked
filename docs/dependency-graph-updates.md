# Successive dependency advisory updates

The October 25 update resolves fast-uri 3.1.9 in both active image-CLI fixtures
and the declared mirrored dependency graph. Each complete graph passed normal
npm resolution, installation with lifecycle scripts disabled, and a fresh
advisory scan. Both runs passed all nine existing runtime controls with Node
26.12.1 and npm 12.2.1. Provider responses were intercepted; no real model or
paid service was called.

The mirror publisher previously permitted only the first dependency repair.
It now accepts a subsequent graph when its declared predecessor matches the
catalog and its previous mirror hash matches the current package. Wrong or
missing predecessors are rejected. The source checkout, original skill text,
complete declaration/lock pair and every nondependency resource retain their
existing verification requirements. Replaying a completed publication remains
idempotent.

The [qualification record](../artifacts/research/2026-10-25/image-cli-fast-uri-qualification.json)
links the two new graph results. Exact prior fixture bytes are retained in the
[historical bundle](../artifacts/research/2026-10-25/image-cli-prior-graph-bytes.json),
with their original paths, source revision and SHA-256 values. Existing dated
runtime receipts remain unchanged and describe their original graphs. Historical
evidence is not an installable current dependency declaration or a current
advisory result.

No scanner rule, path exemption or alert dismissal was added. GitHub must analyze
the exact published default branch before hosted alerts can be considered fixed.
The bot PR's three individual lock edits are not sufficient on their own:
the catalog, manifests, source lock, declared graph and review ledger must agree.

The two negative controls still reproduce short-key masking crashes and false
success after failed image QA. These dependency updates do not repair those
implementation defects or establish coding-agent effectiveness. The changed
package signature invalidated the previous review binding; its prior review is
retained as superseded, with fresh dependency research recorded as incomplete.
