from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "artifacts/external-benchmark-integrations/swe-verified-schema-v1/reproduce.py"
)
spec = importlib.util.spec_from_file_location("swebench_schema_control", SCRIPT)
assert spec is not None and spec.loader is not None
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


def test_recorded_control_and_observation_are_bound() -> None:
    root = SCRIPT.parent
    sources = json.loads((root / "source-observations.json").read_text(encoding="utf-8"))

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

    assert digest(SCRIPT) == sources["control_sha256"]
    assert digest(root / "result.json") == sources["result_sha256"]
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    assert result["cases"]["legacy"]["counts"] == {"KeyError: 'image'": 500}
    assert result["cases"]["current"]["counts"] == {"accepted": 500}
    assert result["agent_efficacy_scored"] is False
    assert result["executes_evaluation_scripts"] is False


def make_pages(directory: Path) -> None:
    for offset in range(0, 500, 100):
        rows = [
            {
                "row_idx": i,
                "truncated_cells": [],
                "row": {"instance_id": f"sample-{i}", "repo": "example/project", "base_commit": "a" * 40},
            }
            for i in range(offset, offset + 100)
        ]
        (directory / f"current-{offset}.json").write_text(
            json.dumps({"num_rows_total": 500, "partial": False, "rows": rows}), encoding="utf-8"
        )


def test_complete_pages_contain_500_unique_rows(tmp_path: Path) -> None:
    make_pages(tmp_path)
    rows, hashes = control.load_pages(tmp_path, "current")
    assert len(rows) == 500
    assert len(hashes) == 5
    assert rows[0]["instance_id"] == "sample-0" and rows[-1]["instance_id"] == "sample-499"


@pytest.mark.parametrize("defect", ["partial", "truncated", "reordered", "duplicate", "missing"])
def test_incomplete_or_ambiguous_pages_are_rejected(tmp_path: Path, defect: str) -> None:
    make_pages(tmp_path)
    path = tmp_path / "current-100.json"
    page = json.loads(path.read_text(encoding="utf-8"))
    if defect == "partial":
        page["partial"] = True
    elif defect == "truncated":
        page["rows"][0]["truncated_cells"] = ["eval_script"]
    elif defect == "reordered":
        page["rows"][0]["row_idx"] = 101
    elif defect == "duplicate":
        page["rows"][0]["row"]["instance_id"] = "sample-0"
    else:
        page["rows"].pop()
    path.write_text(json.dumps(page), encoding="utf-8")
    with pytest.raises(ValueError):
        control.load_pages(tmp_path, "current")
