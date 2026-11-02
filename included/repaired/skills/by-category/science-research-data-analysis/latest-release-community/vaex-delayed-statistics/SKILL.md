---
name: vaex-delayed-statistics
description: Schedule and execute selected Vaex statistics explicitly for a CSV input.
license: MIT
---

# Vaex: explicitly delayed statistics

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the
repository root and retain the required execution evidence.

This maintained overlay covers selected CSV and delayed-statistic examples from
the [locked Vaex skill](provenance/original.SKILL.md), its
[performance reference](provenance/original.performance.md) and
[I/O reference](provenance/original.io_operations.md). It was tested with
`vaex-core` 4.19.0 and Python 3.12 in the recorded Windows and Linux
environments. It is not a full review or an agent-performance result.

A virtual column or expression can be lazy, but a call such as
`df.value.mean()` computes its result by default. Assigning that result to a
second variable does not defer the calculation. To schedule supported
statistics, request `delay=True`, execute the dataset and then obtain each
resolved result.

## Read a CSV and schedule two statistics

The input path is a local CSV with a numeric `value` column. Confirm its schema,
null and missing-value treatment, units, and data provenance before interpreting
the results. This example assumes the column is nonempty and contains finite
values; its mean and sum are computed over all rows.

```python
import vaex

df = vaex.open(str(input_csv))
mean_job = df.value.mean(delay=True)
sum_job = df.value.sum(delay=True)
df.execute()
mean_value = float(mean_job.get())
sum_value = float(sum_job.get())
```

Vaex's CSV reader may inspect the input to infer metadata before later
calculations. Batching these two delayed operations can reduce repeated passes,
but actual memory use and performance depend on the input, operations and
environment. Measure them before claiming larger-than-memory behavior.

`vaex-core` 4.19.0 declares Python `>=3.9,<3.13` and constrains Dask below
2024.9. Use a separately resolved environment when those requirements conflict
with other tools. Its `aplus` dependency was available only as a source
distribution in the tested environment; the published package metadata did not
declare a license, so review redistribution terms separately.
