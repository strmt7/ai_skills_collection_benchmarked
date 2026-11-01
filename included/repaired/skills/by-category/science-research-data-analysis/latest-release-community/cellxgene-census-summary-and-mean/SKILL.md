---
name: cellxgene-census-summary-and-mean
description: Read Census summary counts and compute a zero-filled overall raw-matrix mean with the correct denominator.
license: MIT
---

# CELLxGENE Census summary and raw-matrix mean

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

Pin the Census build and record the chosen organism, measurement, filters and
layer. This focused repair covers summary counts and one descriptive matrix
mean; it does not validate other workflows in the source skill.

## Read a summary count

For an open Census collection `census`, the summary is a table of `label` and
`value` rows. Convert the selected count to an integer:

```python
summary = census["census_info"]["summary"].read().concat().to_pandas()
summary_values = summary.set_index("label")["value"]
total_cell_count = int(summary_values.loc["total_cell_count"])
```

## Describe the selected raw matrix

For an open RNA `ExperimentAxisQuery` named `query`, this computes one overall
mean across all selected cell-by-feature positions, including implicit zero
fill values. It is not a per-gene mean. Reject an empty query rather than
reporting a misleading zero:

```python
import math
import numpy as np

n_positions = query.n_obs * query.n_vars
if not n_positions:
    raise ValueError("Cannot average an empty cell-by-feature selection")
total = math.fsum(
    float(np.sum(batch["soma_data"].to_numpy(), dtype=np.float64))
    for batch in query.X("raw").tables()
)
mean_expression = total / n_positions
```

Raw matrices use sparse zero fill: averaging only returned entries computes a
nonzero-entry mean instead. This matrix-wide zero-filled mean is a descriptive
choice, not automatically a biological expression estimate. Genes absent from
source datasets can be represented as zero in the combined matrix. Use the
feature dataset presence information and an appropriate measured-cell
denominator for a per-gene analysis; do not silently treat unmeasured genes as
measured zeros. When grouping per gene, map SOMA join IDs to query positions
using the query indexer rather than treating join IDs as array offsets.

See the [Census schema](https://chanzuckerberg.github.io/cellxgene-census/cellxgene_census_schema.html)
and the [incremental computation tutorial](https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_compute_over_X.html).
