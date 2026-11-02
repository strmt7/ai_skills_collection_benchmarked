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

## Additional public-source observation

On 2 November 2026, a separate [source-bound inventory](../artifacts/research/2026-11-02/nonsecurity-upstream-v1/manifest.json)
examined 49 selected non-security skills from 15 public sources omitted from
the earlier three-source comparison. Thirteen source comparisons covering 47
skills completed; two source endpoints returned HTTP 404. A 404 does not prove
whether a repository was deleted, renamed, or made private.

For `browser-act/skills`, 31 entrypoints were missing at their recorded paths.
Each had exactly one same-named candidate with identical complete directory Git
entries at the observed head. This identifies byte-identical candidates, not a
review of their meaning or a decision to update the catalog. The remaining
selected browser directory changed at its recorded path. Published releases of
`Bria-AI/bria-skill` and `guinacio/claude-image-gen` also differ from their
locked source versions. `lackeyjb/playwright-skill` has a changed default
branch, but its latest release remains the pinned v5.0.0.

Two old repository names returned GitHub HTTP 301 responses. Their redirect
targets resolved to matching repository IDs, and the canonical repositories
contained the previously pinned commits. The separate canonical-name comparison
uses a **derived alias lock**, retained compressed with the evidence; it is not
the catalog's source lock. The first name's selected directory was unchanged at
head, while the second changed. Redirects and tree equality do not establish
license compatibility, runtime quality or agent effectiveness.

The original-name complete set and the derived-alias set were independently
reconciled against their retained native API streams and reproduced by offline
replay. The manifest binds selections, captured comparison summaries, redirect
evidence and verification records. Native streams for the full Git trees are
retained outside Git; their digests remain in the summaries. No mirrors or
source pins were changed by this observation. The ledger records source-tree
research as in progress, not as a completed skill evaluation.

## Selected skills from mixed-purpose sources

A further [source-bound observation](../artifacts/research/2026-11-02/mixed-upstream-v1/manifest.json)
compared 82 selected non-security skills from five public sources on 2 November
2026. Security-labeled entries were excluded from the selection. Complete
Git-tree comparisons cover all 82 selected skills; the capture of the renamed
`affaan-m/ECC` repository uses a separately retained derived alias lock after
GitHub's permanent redirect and pinned commit were verified.

The selected `ahmedasmar/devops-claude-skills` directories matched their pinned
head. For `akin-ozer/cc-devops-skills`, the latest release remained the pinned
v1.0.0, while 12 selected directories differed at the default-branch head.
The selected `nextlevelbuilder/ui-ux-pro-max-skill` directories differed at the
observed v2.15.0 release, and all selected `affaan-m/ECC` directories differed
at the observed v2.2.3 release. These comparisons do not constitute admission
or a content review of either release.

All 26 selected `Varnan-Tech/opendirectory` entrypoints were missing at their
recorded paths; 21 had same-named candidates and five had none in the captured
complete tree. Candidate names alone do not establish equivalence or deletion.
The complete and alias comparisons were independently reconciled and replayed;
full native tree streams remain outside Git with their digests in the retained
summaries. No catalog pin or mirror was changed, and the ledger records this
as in-progress source research rather than an evaluation.
