# CELLxGENE Census summary and sparse-mean review

The locked CELLxGENE Census skill from `K-Dense-AI/scientific-agent-skills`
at `eb20fb0dcb0b1dadaa3db2737188f0755bbc4770` contains two problematic
examples. The [Census schema](https://chanzuckerberg.github.io/cellxgene-census/cellxgene_census_schema.html)
defines summary metadata as `label` and `value` rows. The pinned example
instead accesses `total_cell_count` as a column. The schema also specifies
zero-filled sparse raw matrices without explicitly stored zero values. The
pinned incremental mean divides by the number of stored values, so it is a
stored-entry mean rather than a mean across all selected matrix positions.

The [focused maintained overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/cellxgene-census-summary-and-mean/SKILL.md)
corrects these two cases. Its [native component control](../artifacts/repaired-skill-readiness/census-summary-mean-v1/reproduce.py)
executes the examples against local SOMA tables and a sparse experiment. It
compares the result with independently constructed dense matrices, checks
noncontiguous join IDs, zero-only data and empty selections, and reproduces
both original failures or differences. The [qualification record](../artifacts/repaired-skill-readiness/census-summary-mean-v1/qualification.json)
states the tested environment and limits.

The zero-filled mean treats each selected matrix position equally. In a
multi-dataset biological analysis, features may not be present in every source
dataset; consult the [dataset presence guidance](https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_dataset_presence.html)
and define an appropriate measured-cell denominator. SOMA join IDs are not
array positions; the [incremental computation guide](https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_compute_over_X.html)
explains the query indexer.

The newer upstream `v2.72.0` candidate at
`526ebce143bc326f44471554e33d66a19c840360` moves the examples to a reference,
uses the summary label correctly and no longer includes the problematic mean
example. This observation does not qualify the full skill or its migration.
An apparent third defect was not reproduced: with TileDB-SOMA 2.3.0, a local
filter-and-projection test returned the filter columns alongside the requested
column, consistent with the displayed result in the
[official query tutorial](https://chanzuckerberg.github.io/cellxgene-census/notebooks/api_demo/census_query_extract.html).

The summary and mean control tests synthetic local SOMA objects, not a live
Census service, biological validity or agent performance.

## Importing AnnData into SOMA

In the separate [ingestion controls](../artifacts/research/2026-11-02/soma-anndata-ingestion/reproduce.py),
TileDB-SOMA 2.3.0 with AnnData 0.13.4 failed for both `from_anndata` and
`from_h5ad` on synthetic dense and sparse inputs. Each failure left a partial
destination. The same four cases with AnnData 0.12.19 round-tripped the tested
matrix, named layer, observation metadata and feature metadata; input H5AD
bytes were unchanged. These controls cover two dependency pairs and small
fixtures, not every dataset or platform.
The CI `known-error` case passes when it observes the expected failure; it is
not a successful import or evidence that the incompatible pair works.

[AnnData 0.13](https://scverse.org/blog/2026-anndata-013/) exposes `X` as the
`None` layer key. The [open TileDB-SOMA issue](https://github.com/single-cell-data/TileDB-SOMA/issues/4466)
describes the incompatible layer-name handling. If your task needs these
ingestion APIs, use a separately qualified environment and verify your own
data and dependencies. The tested `tiledbsoma==2.3.0`, `anndata==0.12.19`
pair is one option until upstream resolves the incompatibility; it is not a
general instruction to downgrade unrelated AnnData workflows. Do not treat a
partial destination as a completed import or delete a destination without
confirming that it belongs to the failed attempt.
