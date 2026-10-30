# AnnData 10x reader review

This partial review concerns the pinned AnnData skill from
`K-Dense-AI/scientific-agent-skills`, commit
`eb20fb0dcb0b1dadaa3db2737188f0755bbc4770`. Its mirrored entrypoint has
SHA-256 `801ad688e978d54f92af466fe2ae13ae7c322100bea6fc7a6004e3c591e8264a`.
The source mirror remains unchanged.

## Finding and upstream update

The mirrored entrypoint and its I/O reference call `ad.read_10x_h5(...)` after
importing `anndata as ad`. In an isolated Windows test with AnnData 0.13.4 and
Scanpy 1.12.5, that call raised `AttributeError`: AnnData did not expose the
named function. The documented [Scanpy 10x HDF5 reader](https://scanpy.readthedocs.io/en/stable/generated/scanpy.read_10x_h5.html)
is `scanpy.read_10x_h5`.

The upstream latest release reported on 30 October 2026 was `v2.72.0`, at
commit `526ebce143bc326f44471554e33d66a19c840360`. Its
[relocated entrypoint](https://github.com/K-Dense-AI/scientific-agent-skills/blob/526ebce143bc326f44471554e33d66a19c840360/skills/anndata/SKILL.md)
and [I/O reference](https://github.com/K-Dense-AI/scientific-agent-skills/blob/526ebce143bc326f44471554e33d66a19c840360/skills/anndata/references/io_operations.md)
use `sc.read_10x_h5` for these examples. The respective Git blob IDs are
`c07814b8785967d62a172692fb5d3a948c3bb12e` and
`aa83cde335c8b1c5b7ac9c47a20bee74745e3a27`. This confirms the specific
upstream change, not the correctness of all other changes in that release.
Updating the source lock and regenerated mirror requires separate review and
validation of the broader source migration.

## Component control

The [control](../artifacts/research/2026-10-30/anndata-10x-controls/reproduce.py)
creates a small synthetic 10x-format HDF5 matrix, checks the AnnData call's
failure, and checks that Scanpy returns the expected three cells, two genes,
gene IDs and matrix values. Its
[recorded result](../artifacts/research/2026-10-30/anndata-10x-controls/result.json)
identifies the tested Python and package versions. Run it in an isolated Python
environment containing those versions of AnnData and Scanpy:

```text
python artifacts/research/2026-10-30/anndata-10x-controls/reproduce.py
```

The tested environment passed `pip check`; its installed package listing is
retained locally with SHA-256
`e7e9e852aa12e052986cfd867c305924f5750fcd7a4fac003fbbfc822eab725a`.
It is a record of the environment, not a portable, hash-locked dependency
specification. The synthetic fixture is a component control, not a real
dataset, full skill evaluation, or agent benchmark.

The Scanpy documentation was read on 30 October 2026 with Crawl4AI
`0.9.5+catalog.portable4`; its native result returned HTTP 200 and had SHA-256
`ad0961d46e58ada1e7bb5f3b580f1a0d0d6f217e377bea346c0dcbd489c88293`.
The versioned upstream skill files were captured through the Git Data API and
checked against their Git blob IDs. Native captures remain local evidence.
