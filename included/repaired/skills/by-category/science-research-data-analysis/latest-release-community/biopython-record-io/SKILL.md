---
name: biopython-record-io
description: Transform Biopython sequence records while keeping qualities and feature coordinates aligned, and read compressed sequence input explicitly.
license: MIT
---

# Biopython record transformations and compressed input

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow `docs/agent-tools.md` in the repository
root and retain execution evidence.

This maintained overlay covers selected examples from the locked Biopython
skill and its sequence I/O reference. Its controls use Biopython 1.88.
Other Biopython operations and agent effectiveness remain unqualified.

## Reverse a record with its position-dependent data

For a DNA record with features or per-letter annotations, reverse the record:

```python
reversed_record = record.reverse_complement()
```

The returned record adjusts feature locations and strands and reverses per-letter
annotations, including quality scores. Assigning a reverse-complemented sequence
to `record.seq` alone leaves those associated values unchanged. Use sequence-only
operations when only a sequence is intended.

The record operation drops identifiers, descriptions, general annotations and
database cross-references by default. Choose which metadata still describes the
transformed sequence before retaining it through the method's explicit options.
Do not copy every annotation automatically. Confirm the molecule type; protein
sequences do not support reverse complementation.

## Inspect slicing semantics

For supplied zero-based, half-open bounds and a step of one:

```python
sub_record = record[start:end]
```

Per-letter annotations are sliced. Fully contained features are retained with
adjusted coordinates; partially overlapping features are omitted. General
annotations other than molecule type and database cross-references are dropped.
The identifier, name and description are retained, so review whether they remain
appropriate. Decide explicitly how to handle truncated features and metadata
before writing or interpreting the subsequence. Strided slicing has different
feature behavior and is outside these controls.

## Open gzip data as text

For a gzip file known to contain exactly one FASTA record:

```python
import gzip
from Bio import SeqIO

with gzip.open(input_path, "rt", encoding="utf-8") as handle:
    parsed_record = SeqIO.read(handle, "fasta")
```

For multiple or large inputs, iterate `SeqIO.parse(handle, format)` inside the
open handle's context. `SeqIO.read` requires exactly one record. Passing an
ordinary gzip pathname directly to `SeqIO.parse` does not decompress it.
BGZF indexing is a separate feature; ordinary gzip input is not supported by
`SeqIO.index`. Check the actual format and encoding rather than inferring them
from a filename alone.
