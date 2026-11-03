"""Exercise the cache-control evidence and its failure boundaries."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "benchmarks/dependency-regressions/next_turbopack_cache.py"
EVIDENCE = ROOT / "artifacts/research/2026-11-03/next-cache-defaults-v1"


def check(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONTROL), "--output", str(path), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@pytest.mark.parametrize("name", ["windows-result.json", "linux-result.json"])
def test_recorded_controls_match_their_source(name: str) -> None:
    result = check(EVIDENCE / name)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"errors": [], "valid": True}


@pytest.mark.parametrize("change", ["boolean", "missing-version", "config-hash", "source-hash", "module-path"])
def test_altered_evidence_is_rejected(tmp_path: Path, change: str) -> None:
    record = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    if change == "boolean":
        record["versions"]["16.4.4"]["defaults"]["turbopackFileSystemCacheForBuild"]["value"] = 1
    elif change == "missing-version":
        del record["versions"]["16.0.0"]
    elif change == "config-hash":
        record["versions"]["16.1.0"]["config_sha256"] = "0" * 64
    elif change == "source-hash":
        record["reproducer_sha256"] = "0" * 64
    else:
        record["versions"]["16.4.4"]["modules"] = ["node_modules/next/../../outside.js"]
    path = tmp_path / "altered.json"
    path.write_text(json.dumps(record), encoding="utf-8")
    result = check(path)
    assert result.returncode == 1
    assert json.loads(result.stdout)["valid"] is False


def test_invalid_archive_cannot_produce_a_passing_record(tmp_path: Path) -> None:
    (tmp_path / "next-16.0.0.tgz").write_bytes(b"not an npm archive")
    output = tmp_path / "result.json"
    result = subprocess.run(
        [sys.executable, str(CONTROL), "--archives", str(tmp_path), "--node", sys.executable, "--output", str(output)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1
    assert "archive digest mismatch" in json.loads(result.stdout)["errors"][0]
    assert not output.exists()
