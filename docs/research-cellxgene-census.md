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

The control tests synthetic local SOMA objects, not a live Census service,
biological validity or agent performance. In a separate isolated experiment,
`tiledbsoma.io.from_anndata` failed when ingesting a synthetic object with
TileDB-SOMA 2.3.0 and AnnData 0.13.4; the component control creates its SOMA
objects directly and does not establish general ingestion compatibility.
