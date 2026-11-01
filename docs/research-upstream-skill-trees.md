# Upstream skill-tree inventory

This [source-bound inventory](../artifacts/research/2026-11-01/upstream-inventory-v1/summary.json)
compares 334 selected, non-security skills from three public upstream sources
with the source commits locked in this collection. It records the default-branch
head and, separately, GitHub's latest published release where available. The
observation began on 1 November 2026 at 21:19:26 UTC; later upstream changes
are not covered.

| Upstream | Selected skills | Changed entrypoint at recorded path, head | Entrypoint missing at recorded path, head | Latest release observed |
| --- | ---: | ---: | ---: | --- |
| K-Dense-AI/scientific-agent-skills | 134 | 0 | 134 | v2.72.0 |
| microsoft/skills | 162 | 128 | 5 | GitHub returned 404 for latest release |
| composio-community/support-skills | 38 | 0 | 0 | GitHub returned 404 for latest release |

An entrypoint missing at its recorded path is not necessarily a deleted skill.
For 129 of the scientific skills, the captured head and release trees contain a
`SKILL.md` under a folder with the exact same name at a different path. The
inventory lists these as *candidates*, not confirmed relocations or equivalent
instructions. Five have no such candidate in the captured complete trees. All
129 candidate entrypoint blobs differ from their pinned counterparts. The
Microsoft figures include five old paths with no same-named candidate in the
captured head tree. The support source's selected skill directories were all
unchanged even though a repository revision can change for unrelated reasons.

The [selection](../artifacts/research/2026-11-01/upstream-inventory-v1/selection.json)
omits security-related entries and the owner's other repositories for this
pass. It is not an inventory of all 673 catalog skills or of newly added
upstream skills. A tree difference says nothing by itself about quality,
licensing, compatibility or whether an update should be adopted. Original
mirrors and source locks are unchanged.

The separately pinned, third-party Karpathy-guidelines adaptation resolved from
`forrestchang/andrej-karpathy-skills` to `multica-ai/andrej-karpathy-skills`.
Its default-branch head still matched the pinned commit at 21:25:59 UTC, and
the pinned skill bytes matched the historical trial protocol's hash. GitHub's
latest-release endpoint returned 404. See the [baseline observation](../artifacts/research/2026-11-01/upstream-inventory-v1/karpathy-baseline.json).
This source is an adaptation of Karpathy's guidelines, not a repository
attributed to him, and the source check is not an agent benchmark.

The comparator checks commit-to-tree identity, object IDs, modes and paths.
If a recursive tree is truncated, it retrieves the selected subtrees using
complete nonrecursive responses; a truncated nonrecursive response is an error,
not evidence of a removal. Candidate-name search is omitted when the root tree
is incomplete. GitHub documents the [recursive tree limits](https://docs.github.com/en/rest/git/trees?apiVersion=2022-11-28#get-a-tree).
The captured root trees in this observation were complete.

An [independent reconciliation](../artifacts/research/2026-11-01/upstream-inventory-v1/verification.json)
checked 468 skill-tree comparisons and 258 candidate directories against the
retained native responses; a separate offline replay reproduced the inventory
byte-for-byte. Raw API streams remain outside Git; their digests and request
paths are in the inventory. These checks do not verify skill quality or agent
effectiveness.

To capture a new observation, provide a fresh output directory and the actual
UTC start time:

```bash
python tools/compare_upstream_skill_trees.py --source-lock data/source_lock.json --selection artifacts/research/2026-11-01/upstream-inventory-v1/selection.json --output /path/to/new-capture --observed-at-utc 2026-11-01T21:19:26Z
```

The example timestamp identifies the recorded observation; replace it for a
new capture. A previous capture can be rechecked without network access by
adding `--replay /path/to/previous-capture` and retaining its original time,
selection and source-lock bytes. `tools/verify_upstream_skill_inventory.py`
independently reconciles captures with complete root trees; it rejects truncated
roots rather than checking the comparator's subtree fallback.
