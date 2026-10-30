# AnnData input and output review

This partial review concerns the pinned AnnData skill from
`K-Dense-AI/scientific-agent-skills`, commit
`eb20fb0dcb0b1dadaa3db2737188f0755bbc4770`. Its mirrored entrypoint has
SHA-256 `801ad688e978d54f92af466fe2ae13ae7c322100bea6fc7a6004e3c591e8264a`.
The source mirror remains unchanged.

## Finding and upstream update

The mirrored entrypoint and its I/O reference call `ad.read_10x_h5(...)` after
importing `anndata as ad`; the reference also calls `ad.read_10x_mtx(...)`.
In an isolated Windows test with AnnData 0.13.4 and Scanpy 1.12.5, both calls
raised `AttributeError`: AnnData did not expose either function. The documented
Scanpy readers are
[`scanpy.read_10x_h5`](https://scanpy.readthedocs.io/en/stable/generated/scanpy.read_10x_h5.html)
and [`scanpy.read_10x_mtx`](https://scanpy.readthedocs.io/en/stable/generated/scanpy.read_10x_mtx.html).

The upstream latest release reported on 30 October 2026 was `v2.72.0`, at
commit `526ebce143bc326f44471554e33d66a19c840360`. Its
[relocated entrypoint](https://github.com/K-Dense-AI/scientific-agent-skills/blob/526ebce143bc326f44471554e33d66a19c840360/skills/anndata/SKILL.md)
and [I/O reference](https://github.com/K-Dense-AI/scientific-agent-skills/blob/526ebce143bc326f44471554e33d66a19c840360/skills/anndata/references/io_operations.md)
use the corresponding Scanpy readers for these examples. The respective Git blob IDs are
`c07814b8785967d62a172692fb5d3a948c3bb12e` and
`aa83cde335c8b1c5b7ac9c47a20bee74745e3a27`. This confirms the specific
upstream change, not the correctness of all other changes in that release.
Updating the source lock and regenerated mirror requires separate review and
validation of the broader source migration.

The mirror also uses top-level `ad.read_csv` and `ad.read_mtx`. These still
resolved in the tested version but emitted deprecation warnings; the
[AnnData release notes](https://anndata.readthedocs.io/en/stable/release-notes/)
direct these imports to `anndata.io`. The upstream I/O reference uses those
newer imports. The test did not exercise every other documented reader.

Two additional examples in the mirrored I/O reference fail with AnnData
0.13.4: `read_mtx` does not accept `var_names` or `obs_names` keywords, and
`read_excel` requires a `sheet` argument. The current documented signatures
for [Matrix Market](https://anndata.readthedocs.io/en/stable/generated/anndata.io.read_mtx.html)
and [Excel](https://anndata.readthedocs.io/en/stable/generated/anndata.io.read_excel.html)
match the reproduced errors. The newer upstream reference reads the matrix and
metadata separately and specifies the Excel sheet.

The mirrored element-level examples import `read_elem` and `write_elem` from
the top-level `anndata` module, where they are absent in the tested version.
They also pass a path string to `read_elem`. The documented
[`anndata.io.read_elem`](https://anndata.readthedocs.io/en/stable/generated/anndata.io.read_elem.html)
expects a stored element; the control writes and reads an HDF5 dataset through
`anndata.io` and reproduces the string-argument failure. The newer upstream
reference imports these functions from `anndata.io` and passes open-store
objects.

The mirrored reference also says that assigning to `adata.obs` in backed
`r+` mode writes the metadata change to disk. In a close-and-reopen control,
the new observation column was absent, even though an in-place dense `X`
change persisted. An explicit write to a new H5AD file preserved the column.
The [backed-mode documentation](https://anndata.readthedocs.io/en/stable/generated/anndata.io.read_h5ad.html)
states that changes to slots such as `obs` are not saved automatically in
backed mode. The newer upstream reference tells readers to write a new file for
metadata changes. Do not rely on the pinned example to persist annotations.

## Component control

The [control](../artifacts/research/2026-10-30/anndata-10x-controls/reproduce.py)
creates small synthetic 10x-format HDF5 and Matrix Market inputs, checks both
AnnData calls' failures, and checks that Scanpy returns the expected three
cells, two genes, gene IDs and matrix values for each format. It also checks
the two top-level import warnings and the availability of their `anndata.io`
counterparts. Its
[recorded result](../artifacts/research/2026-10-30/anndata-10x-controls/result.json)
identifies the tested Python and package versions. Run it in an isolated Python
environment containing those versions of AnnData, Scanpy and openpyxl:

```text
python artifacts/research/2026-10-30/anndata-10x-controls/reproduce.py
```

The control also verifies a generic Matrix Market import with separately
assigned labels, an Excel import with an explicit sheet, an HDF5 element
round-trip, and backed-mode persistence versus an explicit write. The tested
environment passed `pip check`; its installed package listing is
retained locally with SHA-256
`964bd490d9852721cb0909cd0c428de2e0072cbf414d7bf1dc685bb65864594e`.
It is a record of the environment, not a portable, hash-locked dependency
specification. The synthetic fixture is a component control, not a real
dataset, full skill evaluation, or agent benchmark.

The two Scanpy documentation pages, the AnnData release notes and the four
AnnData reader documentation pages were read on 30 October 2026 with Crawl4AI
`0.9.5+catalog.portable4`; each native result returned HTTP 200. Their respective
native-result SHA-256 digests are
`ad0961d46e58ada1e7bb5f3b580f1a0d0d6f217e377bea346c0dcbd489c88293`,
`5722b05d6bc7affa930651682b45e581d065a02c3f12f91d0eac18078017c92d`,
`b2ceba1ae6c0e37e752a7505dac869ed8f0d90f3a08e018185befe82ab62ef79`,
`369f08292281c87460ec1d1df2c14aa1e5d7af257dc8dfb8ce35bfefa9399216`,
`1623580abd9f7fb1701624bb7dab293c4cf58eaa196eebc6203d921096eb3fa5`,
`ffb12d278eadcdacd3b0e3202942639e0cc419b6e81e3ddbc7d5e48774d8e57e`,
and `f49fb99e4c34fd6ea45eedd1e9d433c17720ce2b107c12f926beb491b09154eb`.
The versioned upstream skill files were captured through the Git Data API and
checked against their Git blob IDs. Native captures remain local evidence.
