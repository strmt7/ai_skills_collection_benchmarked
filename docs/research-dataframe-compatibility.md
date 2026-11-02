# Dataframe skill compatibility

The locked Polars, Dask and Vaex skills describe different dataframe systems.
This review checks selected claims and examples; it does not review every bundled
resource or measure an agent's performance. Package versions and observations
are specific to 2 November 2026.

## Polars

With Polars 2.1.0, the locked skill's `collect(streaming=True)` and
`read_csv(..., dtypes=...)` examples fail because those arguments were removed.
The project's [2.0 upgrade guide](https://docs.pola.rs/releases/upgrade/2/)
identifies `engine="streaming"` and `schema_overrides` as their replacements.
The [collect reference](https://docs.pola.rs/api/python/stable/reference/lazyframe/api/polars.LazyFrame.collect.html)
explains engine selection.

The locked best-practices reference also moves a value filter from after a
mean to before that mean. Those queries answer different questions. On the
controlled input, a category with values 50 and 150 has mean 100, but filtering
first leaves a mean of 150. The [maintained Polars overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/polars-lazy-queries/SKILL.md)
keeps the aggregate-first meaning and has synthetic Windows and Linux component
controls. A streaming collection still returns an in-memory result; memory and
performance for a real workload require separate measurement.

## Dask

The locked dataframe reference uses `set_index(..., sorted=True)` without
showing its precondition. Dask's [API reference](https://docs.dask.org/en/stable/generated/dask.dataframe.DataFrame.set_index.html)
specifies that this option is for an already increasing index. In a Windows
Dask 2026.8.0 control with overlapping, unsorted partitions, an indexed lookup
failed; using the default index construction returned the expected row. The
[probe and pinned environment](../artifacts/research/2026-11-02/dataframe-research-v1/)
record that observation. The [maintained index overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/dask-index-queries/SKILL.md)
uses the default index construction and has selected Windows and Linux component
controls. Do not mark data sorted without verifying the required ordering and
divisions. The default construction can require an expensive
[shuffle](https://docs.dask.org/en/latest/dataframe-groupby.html).

## Vaex

The locked performance reference describes an ordinary `mean()` call as
deferred until its result is assigned. In the tested Vaex 4.19.0 environment,
the mean executes at the call; assigning the returned value does not start the
computation. Vaex's [asynchronous guide](https://vaex.io/docs/example_async.html)
documents `delay=True` and explicit execution. The
[delayed-statistics overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/vaex-delayed-statistics/SKILL.md)
tests selected CSV and statistics examples on Windows and Linux. These small
fixtures do not establish out-of-core behavior or performance.

PyPI metadata for `vaex-core` 4.19.0 specifies Python `>=3.9,<3.13` and a
Dask requirement below 2024.9. These constraints apply to that published
package version, not every possible Vaex environment. Check the resolver and
use separate environments when requirements conflict. Its `aplus` dependency
was available as a source distribution only, and its published metadata did
not declare a license; redistribution terms remain to be reviewed.

The [initial source-bound review](../artifacts/research/2026-11-02/dataframe-research-v1/report.json)
records the earlier package observations; the [Vaex qualification](../artifacts/repaired-skill-readiness/vaex-delayed-statistics-v1/qualification.json)
records the later component controls. These are not coding-agent benchmark
scores.
