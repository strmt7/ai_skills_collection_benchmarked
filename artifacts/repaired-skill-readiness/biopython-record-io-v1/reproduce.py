"""Run selected Biopython source examples against independent synthetic expectations."""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import Bio
import numpy
from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature, SimpleLocation
from Bio.SeqRecord import SeqRecord

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/biopython-record-io"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run():
    require(Bio.__version__ == "1.88", "Control requires Biopython 1.88")
    skill = (OVERLAY / "SKILL.md").read_text(encoding="utf-8")
    original = (OVERLAY / "provenance/original.sequence_io.md").read_text(encoding="utf-8")
    blocks = [x.split("```", 1)[0] for x in skill.split("```python\n")[1:]]
    require(len(blocks) == 3, "Expected three maintained snippets")
    record = SeqRecord(
        Seq("AACG"),
        id="read",
        annotations={"molecule_type": "DNA", "source": "sample"},
        dbxrefs=["DB:1"],
        features=[SeqFeature(SimpleLocation(0, 2, strand=1), type="gene")],
        letter_annotations={"phred_quality": [10, 20, 30, 40]},
    )
    line = next(x for x in original.splitlines() if x == "record.seq = record.seq.reverse_complement()")
    bad = copy.deepcopy(record)
    exec(compile(line, "original.sequence_io.md", "exec"), {"record": bad})
    require(
        str(bad.seq) == "CGTT" and bad.letter_annotations["phred_quality"] == [10, 20, 30, 40],
        "Original behavior changed",
    )
    require(
        int(bad.features[0].location.start) == 0 and bad.features[0].location.strand == 1, "Original features changed"
    )
    context = {"record": record, "start": 1, "end": 3}
    exec(compile(blocks[0], "SKILL.md", "exec"), context)
    reverse = context["reversed_record"]
    require(
        str(reverse.seq) == "CGTT" and reverse.letter_annotations["phred_quality"] == [40, 30, 20, 10],
        "Reversed qualities differ",
    )
    location = reverse.features[0].location
    require((int(location.start), int(location.end), location.strand) == (2, 4, -1), "Reversed coordinates differ")
    require(
        reverse.id == "<unknown id>" and reverse.annotations == {} and reverse.dbxrefs == [],
        "Default metadata behavior differs",
    )
    exec(compile(blocks[1], "SKILL.md", "exec"), context)
    sliced = context["sub_record"]
    require(str(sliced.seq) == "AC" and sliced.letter_annotations["phred_quality"] == [20, 30], "Sliced values differ")
    require(
        sliced.annotations == {"molecule_type": "DNA"} and sliced.dbxrefs == [] and sliced.features == [],
        "Slicing metadata behavior differs",
    )
    inner = copy.deepcopy(record)
    inner.features.append(SeqFeature(SimpleLocation(1, 2, strand=1), type="gene"))
    context["record"] = inner
    exec(compile(blocks[1], "SKILL.md", "exec"), context)
    kept = context["sub_record"].features
    require(
        len(kept) == 1 and (int(kept[0].location.start), int(kept[0].location.end)) == (0, 1),
        "Contained feature was not shifted",
    )
    with tempfile.TemporaryDirectory(prefix="biopython-record-control-") as directory:
        path = Path(directory) / "read.fasta.gz"
        with gzip.open(path, "wt", encoding="utf-8") as handle:
            handle.write(">read\nAACG\n")
        from Bio import SeqIO

        require('SeqIO.parse("sequences.fasta.gz", "fasta")' in original, "Original gzip example changed")
        try:
            list(SeqIO.parse(path, "fasta"))
        except (ValueError, UnicodeError) as exc:
            original_error = type(exc).__name__
        else:
            raise ValueError("Direct gzip path unexpectedly succeeded")
        context["input_path"] = path
        exec(compile(blocks[2], "SKILL.md", "exec"), context)
        parsed = context["parsed_record"]
        require(parsed.id == "read" and str(parsed.seq) == "AACG", "Gzip handle round trip differs")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "biopython": Bio.__version__,
        "numpy": numpy.__version__,
        "overlay_sha256": hashlib.sha256((OVERLAY / "SKILL.md").read_bytes()).hexdigest(),
        "reference_sha256": hashlib.sha256((OVERLAY / "provenance/original.sequence_io.md").read_bytes()).hexdigest(),
        "checks": [
            "original_sequence_only_leaves_qualities_and_features",
            "record_reverse_complement_updates_values",
            "reverse_default_metadata",
            "slice_annotation_loss",
            "gzip_text_handle_round_trip",
        ],
        "original_gzip_path_error": original_error,
        "full_skill_reviewed": False,
        "agent_performance_tested": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
