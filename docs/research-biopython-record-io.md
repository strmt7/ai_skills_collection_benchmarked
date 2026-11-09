# Biopython sequence-record and gzip controls

The locked Biopython reference shows assigning a reverse-complemented sequence
to `record.seq`, describes slicing as preserving annotations, and passes a gzip
pathname directly to `SeqIO.parse`.

With Biopython 1.88, the sequence assignment reverses bases while leaving quality
scores and feature locations unchanged. The record-level `reverse_complement`
operation reverses qualities and adjusts feature coordinates and strands.
Slicing retains only selected metadata and fully contained features; it drops
partially overlapping features. These distinctions are documented in the
[SeqRecord API](https://biopython.org/docs/latest/api/Bio.SeqRecord.html).

The gzip-path example failed on the synthetic FASTA fixture. Opening a gzip text
handle explicitly read the expected sequence, consistent with the
[sequence I/O tutorial](https://biopython.org/docs/latest/Tutorial/chapter_seqio.html#parsing-sequences-from-compressed-files).
The [SeqIO API](https://biopython.org/docs/latest/api/Bio.SeqIO.html) separately
documents BGZF indexing and its exclusion of ordinary gzip input.

The [maintained overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/biopython-record-io/SKILL.md)
covers these selected cases and preserves the original entrypoint and sequence
reference. Its [reproduction script](../artifacts/repaired-skill-readiness/biopython-record-io-v1/reproduce.py)
executes the repaired examples against independently specified sequences,
qualities and feature coordinates. The [Windows result](../artifacts/repaired-skill-readiness/biopython-record-io-v1/windows-result.json)
records Python 3.13.17, Biopython 1.88 and NumPy 2.5.4. The adjacent
`requirements-windows.txt` pins the qualified CPython 3.13 Windows wheels with
hashes. Install it into a dedicated virtual environment using
`python -m pip install --require-hashes -r requirements-windows.txt`, then run
`reproduce.py` with that environment's interpreter from this repository.

This is a synthetic component control on Windows. It does not qualify other
Biopython APIs, operating systems, biological datasets or agent performance.
