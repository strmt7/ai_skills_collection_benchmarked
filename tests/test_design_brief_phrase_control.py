"""Keep a reproducible negative control for the unmodified design brief."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/research/2026-11-01/design-brief-phrase"


def test_phrase_control_matches_recorded_platform_observations(tmp_path: Path) -> None:
    output = tmp_path / "result.json"
    script = EVIDENCE / "reproduce.py"
    subprocess.run([sys.executable, "-B", str(script), "--output", str(output)], cwd=ROOT, check=True, timeout=30)
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["expected"] == ["Business Card"]
    assert result["actual"] == ["Business Analytics", "Business Card"]
    assert result["source_satisfies_expected"] is False
    assert result["agent_efficacy_scored"] is False
    for platform in ("windows", "linux"):
        assert result == json.loads((EVIDENCE / f"{platform}-result.json").read_text(encoding="utf-8"))
