import copy
import hashlib
import json
from pathlib import Path

import audit_trial_partitions as target
import pytest


def make_entry(root, task_id, partition, inputs, groups):
    protocol = {
        "task": {"id": task_id, "partition": partition, "brief": "Repair the behavior", "files": list(inputs)},
        "prompt_template": "<TASK_BRIEF>",
        "input_sha256": inputs,
    }
    raw = json.dumps(protocol).encode()
    name = f"{partition}-{task_id}.json"
    (root / name).write_bytes(raw)
    return {
        "id": task_id,
        "partition": partition,
        "protocol": name,
        "protocol_sha256": hashlib.sha256(raw).hexdigest(),
        "groups": groups,
    }


def write_manifest(root, entries):
    path = root / "manifest.json"
    path.write_text(json.dumps({"schema_version": 1, "tasks": entries}), encoding="utf-8")
    return path


def test_actual_development_manifest_is_incomplete():
    manifest = (
        Path(__file__).resolve().parents[1] / "benchmarks/agent-effectiveness/development/partition-manifest.json"
    )
    report = target.audit(manifest)
    assert (report["development_tasks"], report["holdout_tasks"], report["status"]) == (1, 0, "incomplete")
    assert report["potential_overlaps"] == []


def test_renamed_and_reordered_subset_is_reported(tmp_path):
    left = make_entry(tmp_path, "dev", "development", {"a": "a" * 64, "b": "b" * 64}, ["dev-source"])
    right = make_entry(tmp_path, "held", "holdout", {"renamed": "b" * 64}, ["other-source"])
    report = target.audit(write_manifest(tmp_path, [left, right]))
    assert report["status"] == "overlap"
    assert report["potential_overlaps"] == [
        {"development_id": "dev", "holdout_id": "held", "reasons": ["input_content_subset"]}
    ]


def test_declared_group_catches_different_protocol_and_inputs(tmp_path):
    left = make_entry(tmp_path, "dev", "development", {"a": "a" * 64}, ["same-issue"])
    right = make_entry(tmp_path, "held", "holdout", {"b": "b" * 64}, ["same-issue"])
    report = target.audit(write_manifest(tmp_path, [right, left]))
    assert report["potential_overlaps"][0]["reasons"] == ["shared_declared_group"]


def test_distinct_inputs_still_require_independent_review(tmp_path):
    left = make_entry(tmp_path, "dev", "development", {"a": "a" * 64}, ["one"])
    right = make_entry(tmp_path, "held", "holdout", {"b": "b" * 64}, ["two"])
    report = target.audit(write_manifest(tmp_path, [left, right]))
    assert report["status"] == "review_required"
    assert report["potential_overlaps"] == []


def test_same_id_and_task_cannot_be_hidden_by_new_protocol_metadata(tmp_path):
    left = make_entry(tmp_path, "same", "development", {"a": "a" * 64}, ["one"])
    right = make_entry(tmp_path, "same", "holdout", {"a": "a" * 64}, ["two"])
    reasons = target.audit(write_manifest(tmp_path, [left, right]))["potential_overlaps"][0]["reasons"]
    assert reasons == ["same_task_id", "same_declared_task", "same_declared_workspace", "input_content_subset"]


@pytest.mark.parametrize("groups", [[], [""], [" a "], ["x", "x"], [True]])
def test_malformed_groups_are_rejected(tmp_path, groups):
    entry = make_entry(tmp_path, "dev", "development", {"a": "a" * 64}, groups)
    with pytest.raises(ValueError, match="source groups"):
        target.audit(write_manifest(tmp_path, [entry]))


def test_protocol_hash_and_identity_are_verified(tmp_path):
    entry = make_entry(tmp_path, "dev", "development", {"a": "a" * 64}, ["one"])
    changed = copy.deepcopy(entry)
    changed["id"] = "another"
    with pytest.raises(ValueError, match="identity"):
        target.audit(write_manifest(tmp_path, [changed]))
    (tmp_path / entry["protocol"]).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="digest"):
        target.audit(write_manifest(tmp_path, [entry]))


def test_duplicate_keys_and_duplicate_ids_are_rejected(tmp_path):
    entry = make_entry(tmp_path, "dev", "development", {"a": "a" * 64}, ["one"])
    with pytest.raises(ValueError, match="Duplicate task ID"):
        target.audit(write_manifest(tmp_path, [entry, entry]))
    path = tmp_path / "duplicate.json"
    path.write_text('{"schema_version":1,"schema_version":1,"tasks":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        target.audit(path)
