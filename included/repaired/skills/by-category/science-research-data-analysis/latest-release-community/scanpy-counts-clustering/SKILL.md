---
name: scanpy-counts-clustering
description: Preserve identified single-cell counts through Scanpy normalization and compute Leiden labels before plotting a UMAP.
license: MIT
---

# Scanpy counts and clustering

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

This focused overlay corrects two examples in the pinned Scanpy skill. It is not
a complete analysis pipeline or a review of the other source examples.

## Preserve identified counts

Confirm that `adata.X` contains the intended raw count matrix from the data's
provenance; do not infer provenance merely from its numeric values. Choose a new
layer name if `counts` already exists. The following creates an independent
count layer and a separate log-normalized snapshot of the current variables:

```python
import scanpy as sc

if "counts" in adata.layers:
    raise ValueError("Choose a new layer name; counts already exists")
adata.layers["counts"] = adata.X.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
adata.raw = adata.copy()
```

Here `.raw` contains the log-normalized matrix, not the original counts. Layers
follow gene subsetting, while `.raw` keeps its variables; retain a full-gene
count dataset separately if the later analysis needs it. These copies require
memory proportional to the selected data. Choose normalization and downstream
statistics appropriate to the experimental design.

## Cluster before coloring by cluster

After quality control and normalization, choose valid `n_pcs`, `n_neighbors`
and `resolution` values for the data. The example requires the Scanpy Leiden
dependencies and enough observations and variables for the selected parameters:

```python
import scanpy as sc

sc.pp.pca(adata, n_comps=n_pcs, random_state=0)
sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=n_pcs, random_state=0)
sc.tl.umap(adata, random_state=0)
sc.tl.leiden(adata, resolution=resolution, flavor="igraph", n_iterations=2, directed=False, random_state=0)
sc.pl.umap(adata, color="leiden", show=False)
```

The Leiden call creates the label used by the plot. Clusters are exploratory;
they are not verified cell types or independent biological replicates. Assess
stability and interpret results in the context of the data and design.

See the [AnnData `.raw` API](https://anndata.readthedocs.io/en/stable/generated/anndata.AnnData.raw.html),
[Leiden API](https://scanpy.readthedocs.io/en/stable/generated/scanpy.tl.leiden.html)
and [UMAP plotting API](https://scanpy.readthedocs.io/en/stable/api/generated/scanpy.pl.umap.html).
The component controls use synthetic data and do not establish biological validity
or agent effectiveness. The original source entrypoint remains in `provenance/`.
