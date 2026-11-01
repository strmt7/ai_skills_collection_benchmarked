from __future__ import annotations

import json
import runpy
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/research/2026-11-01/design-search"
CONTROL = runpy.run_path(str(EVIDENCE / "reproduce.py"))


def test_recorded_observations_match_the_current_source():
    observed = CONTROL["run_control"](CONTROL["SOURCE"])
    recorded = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    manifest = json.loads((EVIDENCE / "source-manifest.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_text(encoding="utf-8"))
    signature = ledger["skills"][manifest["skill_id"]]["source_signature"]
    assert manifest["source_commit"] == signature["commit_sha"]
    assert manifest["files"]["SKILL.md"] == signature["skill_file_sha256"]
    assert observed == recorded
    assert observed["agent_efficacy_scored"] is False
    assert (EVIDENCE / "windows-result.json").read_bytes() == (EVIDENCE / "linux-result.json").read_bytes()


def test_changed_source_is_rejected_before_executing_it(tmp_path, monkeypatch):
    source = tmp_path / "source"
    manifest = json.loads((EVIDENCE / "source-manifest.json").read_text(encoding="utf-8"))
    for name in manifest["files"]:
        destination = source / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONTROL["SOURCE"] / name, destination)
    altered = source / "scripts/cip/core.py"
    altered.write_bytes(altered.read_bytes() + b"\n# changed fixture\n")
    monkeypatch.setitem(CONTROL["run_control"].__globals__, "capture", lambda *args: pytest.fail("source executed"))
    with pytest.raises(ValueError, match="Source differs"):
        CONTROL["run_control"](source)
