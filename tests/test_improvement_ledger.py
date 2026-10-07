from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

import manage_improvement_ledger as ledger
import pytest


def entry(skill_id="one", commit="a" * 40):
    return {
        "id": skill_id,
        "commit_sha": commit,
        "skill_dir_sha256": "b" * 64,
        "skill_file_sha256": "c" * 64,
        "category": "coding",
        "source_repo": "example/skills",
        "mirrored_path": f"included/skills/{skill_id}",
    }


def test_inventory_covers_each_skill_without_claiming_research():
    result = ledger.synchronize([entry("two"), entry()], {})
    assert list(result["skills"]) == ["one", "two"]
    assert ledger.summary(result)["categories"]["coding"]["research"] == {"pending": 2}
    assert ledger.synchronize([entry(), entry("two")], result) == result


def test_changed_inputs_invalidate_reviews_without_losing_previous_work():
    previous = ledger.synchronize([entry()], {})
    previous["skills"]["one"]["research"] = {"status": "complete", "evidence": [{"path": "evidence.json"}]}
    result = ledger.synchronize([entry(commit="d" * 40)], previous)
    assert result["skills"]["one"]["research"]["status"] == "pending"
    assert result["superseded_reviews"][0]["review"]["research"]["status"] == "complete"
    assert previous["skills"]["one"]["research"]["status"] == "complete"


def test_removed_and_restored_skills_preserve_review_state():
    previous = ledger.synchronize([entry()], {})
    previous["skills"]["one"]["revision"]["status"] = "in_progress"
    retired = ledger.synchronize([], previous)
    assert not retired["skills"]
    assert "one" in retired["retired_skills"]
    restored = ledger.synchronize([entry()], retired)
    assert restored["skills"]["one"]["revision"]["status"] == "in_progress"
    assert not restored["retired_skills"]


def test_duplicate_catalog_ids_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        ledger.synchronize([entry(), entry()], {})


def test_time_gate_opens_only_at_exact_restriction_boundary():
    data = {"time_gates": [{"id": "other-repositories", "not_before_utc": "2026-10-02T12:47:13Z"}]}
    assert not ledger.gate_open(data, "other-repositories", ledger.parse_utc("2026-10-02T12:47:12Z"))
    assert ledger.gate_open(data, "other-repositories", ledger.parse_utc("2026-10-02T12:47:13Z"))
    with pytest.raises(ValueError, match="exactly one"):
        ledger.gate_open(data, "unknown", datetime.now(UTC))
    with pytest.raises(ValueError, match="aware"):
        ledger.gate_open(data, "other-repositories", datetime(2026, 10, 2))


@pytest.mark.parametrize("value", ["2026-10-02T12:47:13", "2026-10-02T14:47:13+02:00"])
def test_gate_rejects_ambiguous_or_non_utc_timestamps(value):
    with pytest.raises(ValueError, match="explicit UTC"):
        ledger.parse_utc(value)


def test_finished_status_requires_existing_unchanged_evidence(tmp_path):
    data = ledger.synchronize([entry()], {})
    record = data["skills"]["one"]["research"]
    record["status"] = "complete"
    assert any("requires evidence" in error for error in ledger.validate(data, tmp_path))
    proof = tmp_path / "research.json"
    proof.write_text("independent evidence", encoding="utf-8")
    record["evidence"] = [{"path": "research.json", "sha256": hashlib.sha256(proof.read_bytes()).hexdigest()}]
    assert not ledger.validate(data, tmp_path)
    proof.write_text("changed", encoding="utf-8")
    assert any("hash mismatch" in error for error in ledger.validate(data, tmp_path))
    record["evidence"] = [{"path": "../outside.json", "sha256": "a" * 64}]
    assert any("external evidence" in error for error in ledger.validate(data, tmp_path))


@pytest.mark.parametrize(
    "bad", [[], {"skills": []}, {"skills": {"one": []}}, {"time_gates": {}}, {"time_gates": [None]}]
)
def test_malformed_ledger_returns_validation_errors(bad, tmp_path):
    assert ledger.validate(bad, tmp_path)


def test_invalid_phase_status_does_not_crash_or_overwrite_ledger(tmp_path, capsys):
    data = ledger.synchronize([entry()], {})
    data["skills"]["one"]["research"]["status"] = ["complete"]
    path = tmp_path / "ledger.json"
    original = json.dumps(data)
    path.write_text(original, encoding="utf-8")
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps([entry()]), encoding="utf-8")
    assert ledger.main(["--ledger", str(path), "--catalog", str(catalog), "--json"]) == 1
    assert "invalid status" in capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "bad", [[], {"time_gates": {}}, {"time_gates": [None]}, {"time_gates": [{"id": "gate", "not_before_utc": None}]}]
)
def test_malformed_gate_fails_closed(bad):
    with pytest.raises(ValueError):
        ledger.gate_open(bad, "gate", datetime.now(UTC))


def resource_ledger(tmp_path):
    data = ledger.synchronize([entry()], {})
    mirror = tmp_path / data["skills"]["one"]["mirrored_path"]
    mirror.mkdir(parents=True)
    for name in ["SKILL.md", "helper.py"]:
        (mirror / name).write_text("controlled resource", encoding="utf-8")
    data["skills"]["one"]["research"]["resources"] = {
        name: {"sha256": hashlib.sha256((mirror / name).read_bytes()).hexdigest(), "status": "pending"}
        for name in ["SKILL.md", "helper.py"]
    }
    return data, mirror


def test_resource_inventory_is_pending_and_covers_helpers(tmp_path):
    data, mirror = resource_ledger(tmp_path)
    assert not ledger.validate(data, tmp_path)
    assert data["skills"]["one"]["research"]["status"] == "pending"
    del data["skills"]["one"]["research"]["resources"]["helper.py"]
    assert any("complete mirrored package" in e for e in ledger.validate(data, tmp_path))
    assert (mirror / "helper.py").exists()


def test_resource_review_detects_changed_helpers(tmp_path):
    data, mirror = resource_ledger(tmp_path)
    (mirror / "helper.py").write_text("changed helper", encoding="utf-8")
    assert any("resource hash mismatch" in e for e in ledger.validate(data, tmp_path))


def test_explicit_canonical_resource_hashes_survive_git_line_endings(tmp_path):
    from build_catalog import sha256_file

    data, mirror = resource_ledger(tmp_path)
    research = data["skills"]["one"]["research"]
    research["resource_hash_policy"] = "catalog-canonical-v1"
    for name, record in research["resources"].items():
        record["captured_raw_sha256"] = record["sha256"]
        record["sha256"] = sha256_file(mirror / name)
    for file in mirror.iterdir():
        file.write_bytes(file.read_bytes().replace(b"\r\n", b"\n"))
    assert not ledger.validate(data, tmp_path)
    helper = mirror / "helper.py"
    helper.write_bytes(helper.read_bytes() + b"\nchanged = True\n")
    assert any("resource hash mismatch" in error for error in ledger.validate(data, tmp_path))


def test_unknown_resource_hash_policy_fails_closed(tmp_path):
    data, _ = resource_ledger(tmp_path)
    data["skills"]["one"]["research"]["resource_hash_policy"] = "unknown"
    assert any("unsupported resource hash policy" in error for error in ledger.validate(data, tmp_path))


@pytest.mark.parametrize("name", ["../outside", "./SKILL.md", "C:/absolute", "helper\\file.py", ""])
def test_resource_paths_are_canonical_and_contained(tmp_path, name):
    data, _ = resource_ledger(tmp_path)
    data["skills"]["one"]["research"]["resources"][name] = {"status": "pending", "sha256": "a" * 64}
    assert any("noncanonical" in e for e in ledger.validate(data, tmp_path))


def test_reviewed_resource_requires_scope_and_complete_review_rejects_pending(tmp_path):
    data, _ = resource_ledger(tmp_path)
    research = data["skills"]["one"]["research"]
    research["resources"]["SKILL.md"]["status"] = "reviewed"
    assert any("concrete review scope" in e for e in ledger.validate(data, tmp_path))
    research["resources"]["SKILL.md"]["review_scope"] = "Complete text and activation contract reviewed"
    assert not ledger.validate(data, tmp_path)
    research["status"] = "complete"
    assert any("pending resources" in e for e in ledger.validate(data, tmp_path))


@pytest.mark.parametrize("record", [[], {"status": []}, {"status": "invented"}])
def test_malformed_resource_status_is_reported(tmp_path, record):
    data, _ = resource_ledger(tmp_path)
    data["skills"]["one"]["research"]["resources"]["helper.py"] = record
    assert any("invalid resource status" in e for e in ledger.validate(data, tmp_path))
