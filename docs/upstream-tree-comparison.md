# Reviewing an upstream source update

Before replacing a source lock, compare the selected skills against the new
upstream commit. This preserves a per-skill list of changed Git resources and
identifies missing entrypoints; it does not decide whether to admit an update.

The [Everything Claude Code comparison](../artifacts/research/2026-10-28/ecc-upstream-tree-delta.json)
covers all 30 skills selected from the pinned `v1.10.0` source and compares them
with `v2.2.3`. All 30 source directories differ, and two selected entrypoints
are absent at their old paths. Each record includes the old and new Git object
IDs and modes for every changed resource. The improvement ledger links this
inventory to each affected skill; individual research remains in progress.

## Reproduce a comparison

The recorded comparison includes its exact verifier, GitHub API responses, and source lock
under [source snapshots](../artifacts/research/2026-10-28/ecc-source-snapshots/).
The larger responses are compressed without changing their decompressed bytes.
To verify the recorded result without network access, run:

```powershell
python artifacts/research/2026-10-28/ecc-source-snapshots/generator.py.txt --repo affaan-m/everything-claude-code `
  --lock artifacts/research/2026-10-28/ecc-source-snapshots/source-lock.json.gz `
  --old-commit artifacts/research/2026-10-28/ecc-source-snapshots/old-commit.json `
  --old-tree artifacts/research/2026-10-28/ecc-source-snapshots/old-tree.json.gz `
  --new-commit artifacts/research/2026-10-28/ecc-source-snapshots/new-commit.json `
  --new-tree artifacts/research/2026-10-28/ecc-source-snapshots/new-tree.json.gz `
  --output artifacts/research/2026-10-28/ecc-upstream-tree-delta.json --check
```

In other shells, use their line-continuation syntax or put the arguments on one line.

For a new comparison, use `tools/compare_upstream_trees.py` and capture GitHub
Git Data API responses for the two exact
commits and their root trees. Tree requests must use `?recursive=1`, and the
returned `truncated` value must be false. Do not substitute web-page text for
API responses. The old commit must match the selected source lock. The tool
reconstructs every Git tree object against the root identified by each commit
response. It records hashes of the decompressed input bytes and the tool.
`--check` requires those exact inputs and verifier bytes; the retained verifier
keeps the historical result reproducible if the active tool changes. A fresh API
capture can have a different response hash even if the Git trees are equal.

Commit-to-tree bindings depend on the authenticity of the supplied API
responses; signatures are not verified. The tool supports SHA-1 Git object IDs,
whose matching hashes do not rule out collisions. A directory can include nested skills,
symlinks, or submodules, so this raw comparison is not the catalog's mirror
admission, a content or license review, a runtime test, or an agent benchmark.
Resolve missing paths and validate the entire selected source before updating
the lock. Preserve old source evidence and frozen benchmark inputs.
