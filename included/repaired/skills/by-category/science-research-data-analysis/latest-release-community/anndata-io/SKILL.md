---
name: anndata-io
description: Read 10x data with Scanpy and persist selected AnnData metadata changes when working with backed H5AD files.
license: MIT
---

# AnnData I/O: 10x readers and backed metadata

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

This maintained, narrowly scoped overlay corrects selected I/O examples in the
pinned AnnData skill. It does not replace or validate the rest of that skill.
The original entrypoint and I/O reference are retained in `provenance/`.

## Read 10x data

Install Scanpy in the user's chosen environment when these readers are needed.
For a 10x HDF5 file:

```python
import scanpy as sc

counts_h5 = sc.read_10x_h5(h5_path)
```

For a 10x Matrix Market directory:

```python
import scanpy as sc

counts_mtx = sc.read_10x_mtx(mtx_dir)
```

Inspect observation and feature
names, feature types and matrix dimensions before downstream analysis. The
readers' defaults filter to gene expression; pass the documented arguments if
other feature types are needed. These are Scanpy readers, not AnnData readers.

## Save changes to observation metadata

AnnData backed mode does not automatically persist changes to `obs`. Select a
subset that fits in memory, materialize it, close the backed file, and write to a
new output path. The selection and label below are supplied by the caller:

```python
import anndata as ad

backed = ad.io.read_h5ad(input_path, backed="r")
try:
    subset = backed[obs_selection, :].to_memory()
finally:
    backed.file.close()
subset.obs["sample"] = sample_label
subset.write_h5ad(output_path)
```

Choose a distinct output file and verify the result after reopening it. The
selection determines which observations are written; this example does not
write the complete original dataset unless the selection includes all rows.
Materializing the selection requires enough memory for its data and annotations.
For larger-than-memory changes, choose and validate an appropriate workflow for
the specific data rather than assuming this example will fit.

See the [AnnData backed reader documentation](https://anndata.readthedocs.io/en/stable/generated/anndata.io.read_h5ad.html),
[Scanpy HDF5 reader](https://scanpy.readthedocs.io/en/stable/generated/scanpy.read_10x_h5.html)
and [Scanpy Matrix Market reader](https://scanpy.readthedocs.io/en/stable/generated/scanpy.read_10x_mtx.html).
The recorded component control uses synthetic data; it is not an agent benchmark.
