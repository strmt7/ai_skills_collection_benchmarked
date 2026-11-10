from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import _trial_collection as transport
import pytest
from _trial_collection_manifest import validate_manifest
from _trial_collection_policy import default_collection_policy


@pytest.fixture
def receipt():
    return {
        "collection_version": 1,
        "status": "collected",
        "policy": default_collection_policy(),
        "files": {"src/code.py": {"sha256": hashlib.sha256(b"source").hexdigest(), "bytes": 6}},
        "directories": ["src"],
        "directory_count": 1,
        "excluded": [],
        "file_count": 1,
        "total_bytes": 6,
        "post_inventory_matches": True,
        "atomic_snapshot": False,
        "precondition": "All subject execution must be stopped before capture.",
    }


def test_manifest_accepts_a_complete_canonical_source_namespace(receipt):
    assert validate_manifest(receipt, default_collection_policy()) == receipt


@pytest.mark.parametrize(
    "change",
    [
        "count",
        "size",
        "digest",
        "parent",
        "alias",
        "cache",
        "policy-bool",
        "atomic",
        "depth",
        "exclusion",
        "unlisted-field",
    ],
)
def test_forged_capture_metadata_is_rejected(receipt, change):
    if change == "count":
        receipt["file_count"] = True
    elif change == "size":
        receipt["files"]["src/code.py"]["bytes"] = True
    elif change == "digest":
        receipt["files"]["src/code.py"]["sha256"] = "not-a-digest"
    elif change == "parent":
        receipt["directories"] = []
    elif change == "alias":
        receipt["files"]["SRC/code.py"] = copy.deepcopy(receipt["files"]["src/code.py"])
    elif change == "cache":
        receipt["directories"].append("__pycache__")
    elif change == "policy-bool":
        receipt["policy"]["max_depth"] = True
    elif change == "atomic":
        receipt["atomic_snapshot"] = True
    elif change == "depth":
        receipt["policy"]["max_depth"] = 1
        receipt["files"] = {"src/deeper/file.py": {"sha256": "a" * 64, "bytes": 6}}
        receipt["directories"] = ["src", "src/deeper"]
    elif change == "exclusion":
        receipt["excluded"] = [{"path": "src", "reason": "declared_generated_cache"}]
    else:
        receipt["unknown"] = "not admitted"
    with pytest.raises(ValueError):
        validate_manifest(receipt, default_collection_policy())


@pytest.mark.skipif(sys.platform != "win32", reason="Windows owned collector process")
def test_owned_worker_captures_new_sources_without_inheriting_controller_variables(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    (workspace / "nested").mkdir(parents=True)
    (workspace / "nested/new.py").write_bytes(b"source")
    (workspace / "binary").write_bytes(b"\xff")
    monkeypatch.setenv("COLLECTOR_PARENT_CANARY", "must not cross")
    assert os.environ["COLLECTOR_PARENT_CANARY"] == "must not cross"
    monkeypatch.setattr(
        transport, "BOOTSTRAP", "import os;assert 'COLLECTOR_PARENT_CANARY' not in os.environ;" + transport.BOOTSTRAP
    )
    output, observations = tmp_path / "output", tmp_path / "observations"
    result = transport.capture_owned(workspace, output, observations, Path(sys.executable), default_collection_policy())
    assert result["status"] == "collected" and set(result["files"]) == {"binary", "nested/new.py"}
    assert (output / "nested/new.py").read_bytes() == b"source"
    process = json.loads((observations / "process.json").read_bytes())
    assert process["exit_code"] == 0 and process["job_active_processes_after_cleanup"] == 0
    assert process["explicit_environment"] is True
    assert b"COLLECTOR_PARENT_CANARY" not in (observations / "stdout.native").read_bytes()


@pytest.mark.skipif(sys.platform != "win32", reason="Windows owned collector timeout")
def test_owned_worker_timeout_cannot_produce_a_successful_receipt(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    policy = default_collection_policy()
    policy["timeout_seconds"] = 1
    monkeypatch.setattr(transport, "BOOTSTRAP", "import time;time.sleep(30)")
    observations = tmp_path / "observations"
    result = transport.capture_owned(workspace, tmp_path / "output", observations, Path(sys.executable), policy)
    assert result["status"] == "collection_error"
    process = json.loads((observations / "process.json").read_bytes())
    assert process["termination_reason"] == "timeout" and process["job_active_processes_after_cleanup"] == 0
