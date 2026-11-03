# Zarr Python: selected API review

The locked Zarr skill is preserved at K-Dense commit
`eb20fb0dcb0b1dadaa3db2737188f0755bbc4770`. On 3 November 2026,
selected examples were checked with Zarr Python 3.4.2 and NumPy 2.5.4 in
isolated Windows and Linux environments. The tested source uses separate
resize arguments, `codecs` when creating an array, and a stored-byte method as
an attribute; these examples raise `TypeError`. Its synchronizer imports raise
`ImportError` in that version. These are version-specific observations, not a
complete review of either bundled resource.

The [maintained basics overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/zarr-python-basics/SKILL.md)
uses the tested tuple resize, `compressors` parameter and method call. Its
[component control](../artifacts/repaired-skill-readiness/zarr-python-basics-v1/control.py)
extracts the original statements from the preserved source and executes the
replacement example, checking values against an independent expectation. It is
not an agent benchmark. The original mirror, its exact original entrypoint and
the upstream license are retained; the reference and remaining examples still
need review. The [reference control](../artifacts/repaired-skill-readiness/zarr-python-basics-v1/reference-control.py)
also reproduces missing `copy` and `info_items` methods and a case where
`chunks=None` still creates multiple chunks on both recorded hosts. This
counterexample does not predict chunk shapes for other inputs. Concurrent
writes, persistence, cloud storage, sharding and codec performance were not
tested.

The official [migration guide](https://zarr.readthedocs.io/en/stable/user-guide/v3_migration/)
documents tuple-based resize and describes synchronizer support; the
[array guide](https://zarr.readthedocs.io/en/stable/user-guide/arrays/) documents
compression configuration. The [performance guide](https://zarr.readthedocs.io/en/stable/user-guide/performance/)
sets conditions for concurrent process writes. The tested release's
[package metadata](https://pypi.org/pypi/zarr/3.4.2/json) specifies its Python
requirement. Native research capture hashes and local control results are in the
[qualification record](../artifacts/repaired-skill-readiness/zarr-python-basics-v1/qualification.json).
Documentation at a `stable` URL can change over time.

The upstream skill was inspected separately at release `v2.72.0`, commit
`526ebce143bc326f44471554e33d66a19c840360`: its Zarr entrypoint had already
changed the selected API examples. Its upstream branch and that release had the
same Zarr entrypoint and API-reference Git blobs at observation time. The
upstream repository has moved its skill tree and changed other entries; this
single-skill review does not qualify a whole-source lock refresh. The overlay
does not import the newer source wholesale or establish that its remaining
claims work.
