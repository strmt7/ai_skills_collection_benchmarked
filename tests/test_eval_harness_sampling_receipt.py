"""Verify the source-bound sampling example and its stale-evidence check."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "artifacts/research/2026-11-03/eval-harness-sampling-v1/check_metrics.py"
RESULT = ROOT / "artifacts/research/2026-11-09/eval-harness-sampling-v2/result.json"


def test_sampling_control_checks_current_and_changed_evidence(tmp_path: Path) -> None:
    current = subprocess.run(
        [sys.executable, str(CONTROL), "--check", "--result", str(RESULT)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert current.returncode == 0
    report = json.loads(current.stdout)
    assert report["agent_performance_tested"] is False
    assert report["results"]["subsets_checked"] == 480
    assert report["results"]["unequal_attempts_equal_task_pass1"] == "1/2"
    assert report["results"]["unequal_attempts_pooled_pass1"] == "1/5"
    historical = json.loads(CONTROL.with_name("result.json").read_text(encoding="utf-8"))
    assert report["results"] == historical["results"]

    report["results"]["four_tasks_any5"] = "1"
    changed = tmp_path / "changed.json"
    changed.write_text(json.dumps(report), encoding="utf-8")
    stale = subprocess.run(
        [sys.executable, str(CONTROL), "--check", "--result", str(changed)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert stale.returncode == 1
    assert json.loads(stale.stdout)["error"] == "Sampling-control evidence is stale"
