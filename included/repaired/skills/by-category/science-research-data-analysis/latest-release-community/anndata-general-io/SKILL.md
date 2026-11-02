---
name: anndata-general-io
description: Read generic Matrix Market and Excel data, access HDF5 elements, and combine backed AnnData objects.
license: MIT
---

# AnnData: selected I/O operations

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the
repository root and retain the required execution evidence.

These examples supplement the separate [10x and backed-metadata overlay](../anndata-io/SKILL.md).
They cover selected operations from the [original I/O reference](provenance/original.io_operations.md),
not the complete AnnData skill. The tested version is AnnData 0.13.4; validate
versions, formats, data semantics and outputs for the user's actual dataset.

## Generic Matrix Market input

The following assumes the matrix has **features as rows and observations as
columns**, and each tab-separated label file has exactly one ID per line in
the same order as its corresponding matrix axis. Check those assumptions with
the data producer: matching lengths alone cannot establish correct ordering.
Choose a dtype appropriate for the data and required precision.

```python
import anndata as ad
import pandas as pd

def read_ids(path):
    table = pd.read_csv(path, sep="\t", header=None, dtype=str, keep_default_na=False, skip_blank_lines=False)
    if table.shape[1] != 1 or table[0].eq("").any() or table[0].duplicated().any():
        raise ValueError("ID file must contain one nonempty, unique ID per row")
    return table[0].tolist()

data = ad.io.read_mtx(matrix_path, dtype="float64").T
obs_ids = read_ids(observation_ids_path)
var_ids = read_ids(feature_ids_path)
if data.shape != (len(obs_ids), len(var_ids)):
    raise ValueError("Matrix dimensions do not match the supplied IDs")
data.obs_names = obs_ids
data.var_names = var_ids
```

This is a generic Matrix Market example, not a substitute for Scanpy's 10x
readers. AnnData stores observations in rows and variables in columns.

## Excel input

Supply the sheet explicitly. The example expects the first row and first
column to contain variable and observation names respectively, with numeric
values in the remaining cells. Inspect names, orientation and values before
analysis; `.xlsx` files require an Excel-reading dependency such as openpyxl.

```python
import anndata as ad

data = ad.io.read_excel(workbook_path, sheet=sheet_name)
```

## HDF5 elements

`read_elem` accepts an opened storage element, not a path string. This example
creates a new HDF5 file and reopens it for reading; the caller supplies `values`
and a destination that does not already exist.

```python
import anndata as ad
import h5py

with h5py.File(element_path, "x") as store:
    ad.io.write_elem(store, "values", values)
with h5py.File(element_path, "r") as store:
    restored = ad.io.read_elem(store["values"])
```

## Collection of backed files

Open the files as backed AnnData objects and keep their handles open while
using the collection. This example reads the combined matrix and observation
metadata into memory before closing its inputs; ensure they fit. It does not
copy variable metadata, layers, embeddings or other AnnData fields.
`join_vars="inner"` keeps
shared variables, and `join_obs="inner"` keeps shared observation columns.
Confirm that these choices, feature identities, order and generated observation
IDs are appropriate for the data. `AnnCollection` is experimental.

```python
from contextlib import ExitStack
import anndata as ad
from anndata.experimental import AnnCollection

with ExitStack() as stack:
    datasets = []
    for path in input_paths:
        dataset = ad.io.read_h5ad(path, backed="r")
        stack.callback(dataset.file.close)
        datasets.append(dataset)
    collection = AnnCollection(datasets, join_obs="inner", join_vars="inner", index_unique="-")
    matrix = collection[:].X
    if matrix is None:
        raise ValueError("The selected collection has no X matrix")
    observations = collection.obs.copy()
    variables = collection.var_names.copy()
```

In the tested AnnData 0.13.4 environment, calling `collection[:].to_adata()`
failed on the synthetic backed inputs, so do not assume that operation works
for this version. Test any other fields and materialization paths separately.

The [component controls](../../../../../../../artifacts/repaired-skill-readiness/anndata-general-io-v1/qualification.json)
use synthetic data. They do not establish biological validity, performance on
large datasets, correctness of all file layouts, or coding-agent improvement.
