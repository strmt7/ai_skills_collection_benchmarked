"""Replay the complete public control archive and reject changed native evidence."""

import importlib.util
import json
from pathlib import Path

import pytest

ARCHIVE = Path(__file__).resolve().parents[1] / "artifacts/research/2026-11-25/testeval-collector-cohort"


@pytest.fixture
def archive_verifier():
    spec = importlib.util.spec_from_file_location("testeval_collector_archive_recheck", ARCHIVE / "recheck.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_regrade_every_public_control(archive_verifier) -> None:
    result = archive_verifier.verify(ARCHIVE)
    assert result == json.loads((ARCHIVE / "summary.json").read_bytes())
    assert result["public_tasks"] == 12 and result["control_runs"] == 36
    assert len(result["identical_native_metric_task_ids"]) == 12
    assert result["observations"]["exact"]["detected"] == 24
    assert result["observations"]["shape"]["survived"] == 24
    assert result["observations"]["incorrect"]["detected"] is None
    assert result["model_attempts"] == 0


def test_regrade_rejects_changed_native_stream(archive_verifier, tmp_path: Path) -> None:
    edited = json.loads((ARCHIVE / "native-reports.json").read_bytes())
    report = edited["controls"][0]["reports"]
    report["publisher.stdout"] += "\n"
    (tmp_path / "native-reports.json").write_text(json.dumps(edited), encoding="utf-8")
    with pytest.raises(ValueError, match="Evidence bytes changed for publisher.stdout"):
        archive_verifier.verify(tmp_path)
