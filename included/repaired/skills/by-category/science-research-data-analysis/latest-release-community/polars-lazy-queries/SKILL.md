---
name: polars-lazy-queries
description: Build explicitly typed lazy Polars aggregations while preserving filter semantics and accounting for result materialization.
license: MIT
---

# Polars: lazy aggregation and streaming

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the
repository root and retain the required execution evidence.

This maintained overlay covers selected CSV, lazy aggregation and streaming
examples from the [locked Polars skill](provenance/original.SKILL.md) and its
[best-practices](provenance/original.best_practices.md) and
[I/O](provenance/original.io_guide.md) references. It was tested with Polars
2.1.0 on the recorded Windows and Linux environments; it is not a full review
of the original skill or evidence of improved agent performance.

For Polars 2, use `schema_overrides` instead of the removed `dtypes` argument
and `collect(engine="streaming")` instead of the removed `streaming=True`
argument. The default lazy engine is also streaming in Polars 2, subject to
engine configuration. Verify the actual installed version and its documentation.

## Aggregate first, then filter the aggregate

The input CSV is assumed to have `category` and numeric `value` columns. The
question is which categories have a **mean over all their rows** greater than
100. Confirm this definition and the desired treatment of null values with the
data owner; Polars means ignore null values. Filtering individual rows before
calculating the mean answers a different question.

```python
import polars as pl

source = pl.scan_csv(
    input_csv,
    schema_overrides={"category": pl.String, "value": pl.Float64},
)
means = source.group_by("category").agg(pl.col("value").mean().alias("mean_value"))
selected = means.filter(pl.col("mean_value") > 100).sort("category")
result = selected.collect(engine="streaming")
```

`collect` returns an in-memory DataFrame: the result still has to fit in memory,
and the streaming engine does not guarantee that every query uses bounded
memory. Inspect the plan and measure memory for the actual workload. If the
result is too large to collect, a file sink can avoid returning the full result
to Python, subject to the operation and storage characteristics:

```python
selected.sink_parquet(output_parquet)
```

Choose a suitable destination and verify the resulting data, schema and resource
usage. This example does not establish throughput, out-of-core behavior for
every operator, or compatibility with other Polars releases.
