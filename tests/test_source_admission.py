import hashlib
import json

import _source_admission as admission
import pytest


def held_source(tmp_path):
    evidence = tmp_path / "artifacts/research/held.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(
        json.dumps(
            {
                "source_repo": "owner/repo",
                "source_commit": "a" * 40,
                "source_candidate_state": "held_before_publication",
            }
        ),
        encoding="utf-8",
    )
    record = {
        "source_repo": "owner/repo",
        "source_commit": "a" * 40,
        "reason": "Individual declarations require review",
        "evidence_path": "artifacts/research/held.json",
        "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
    }
    registry = tmp_path / "data/source_admission_holds.json"
    registry.parent.mkdir()
    registry.write_text(json.dumps({"schema_version": 1, "holds": [record]}), encoding="utf-8")
    return evidence, record, registry


def test_exact_held_candidate_is_refused_without_blocking_other_versions(tmp_path):
    held_source(tmp_path)
    with pytest.raises(ValueError, match="source admission held"):
        admission.require_admitted_source(tmp_path, "owner/repo", "a" * 40)
    admission.require_admitted_source(tmp_path, "owner/repo", "b" * 40)
    admission.require_admitted_source(tmp_path, "other/repo", "a" * 40)


@pytest.mark.parametrize("mutation", ["bytes", "external", "identity", "duplicate"])
def test_hold_evidence_cannot_drift_escape_or_change_identity(tmp_path, mutation):
    evidence, record, registry = held_source(tmp_path)
    records = [record]
    if mutation == "bytes":
        evidence.write_bytes(b"Changed evidence")
    elif mutation == "external":
        record["evidence_path"] = "../outside"
    elif mutation == "identity":
        record["source_commit"] = "c" * 40
    else:
        records.append(dict(record))
    registry.write_text(json.dumps({"schema_version": 1, "holds": records}), encoding="utf-8")
    with pytest.raises(ValueError):
        admission.source_holds(tmp_path)
