# Scanpy count provenance and clustering review

This review covers two examples in the pinned Scanpy skill from
`K-Dense-AI/scientific-agent-skills` at commit
`eb20fb0dcb0b1dadaa3db2737188f0755bbc4770`. The original mirror is unchanged.

The pinned normalization example says it saves raw counts, but assigns `.raw`
after normalization and `log1p`. AnnData initializes `.raw` from the current
object, so this snapshot contains the transformed values. The separate
dimensionality-reduction example plots `leiden` before the clustering example
creates that label. When the input has no such observation annotation, the plot
raises `KeyError`. See the [AnnData raw API](https://anndata.readthedocs.io/en/stable/generated/anndata.AnnData.raw.html)
and [Scanpy UMAP plotting API](https://scanpy.readthedocs.io/en/stable/api/generated/scanpy.pl.umap.html).

The [maintained overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/scanpy-counts-clustering/SKILL.md)
keeps an independent count layer before transformation, saves a separate
log-normalized snapshot, and performs Leiden clustering before plotting its
labels. It checks that an existing `counts` layer is not overwritten. The
caller must establish count provenance and choose parameters appropriate to the
data. Gene subsetting also subsets layers, so full-gene counts may need to be
retained separately. See the [Leiden API](https://scanpy.readthedocs.io/en/stable/generated/scanpy.tl.leiden.html).

The [component control](../artifacts/repaired-skill-readiness/scanpy-counts-clustering-v1/reproduce.py)
reproduces the two pinned examples' failures and executes the actual overlay
examples with dense and sparse synthetic matrices. It checks count and snapshot
preservation, an existing layer, real clustering and plotting, and H5AD
round trips. The [qualification record](../artifacts/repaired-skill-readiness/scanpy-counts-clustering-v1/qualification.json)
identifies the tested platforms and dependencies. It is not a biological
validation, complete review of the skill, or agent benchmark.

The upstream `v2.72.0` candidate at commit
`526ebce143bc326f44471554e33d66a19c840360` distinguishes counts from the
log-normalized `.raw` snapshot in its entrypoint. Its `run_pipeline.py`
places Leiden clustering before the Leiden-colored plot. These observations
do not establish that the complete upstream skill or its scripts are correct;
the broader source migration remains separate.

Two initially selected documentation URLs returned 404 or redirected to 404.
Those failed native captures are retained locally; the official paths linked
above were then successfully captured and reviewed with Crawl4AI.
