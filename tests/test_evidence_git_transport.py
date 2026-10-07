"""Every hash-bound ledger input must survive the repository's Git filters."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def evidence_paths(node: Any) -> set[str]:
    paths: set[str] = set()
    if isinstance(node, dict):
        if isinstance(node.get("path"), str) and isinstance(node.get("sha256"), str):
            paths.add(node["path"])
        for value in node.values():
            paths.update(evidence_paths(value))
    elif isinstance(node, list):
        for value in node:
            paths.update(evidence_paths(value))
    return paths


def test_all_ledger_evidence_survives_git_clean_filters() -> None:
    names = sorted(evidence_paths(json.loads((ROOT / "data/improvement_ledger.json").read_bytes())))
    assert names
    inputs = "".join(json.dumps(name, ensure_ascii=False) + "\n" for name in names)
    hashes = []
    for options in (["--no-filters"], []):
        result = subprocess.run(
            ["git", "-c", "core.longpaths=true", "-c", "core.safecrlf=false", "hash-object", *options, "--stdin-paths"],
            cwd=ROOT,
            input=inputs,
            text=True,
            capture_output=True,
            check=True,
            timeout=60,
        )
        assert not result.stderr.strip(), result.stderr
        hashes.append(result.stdout.splitlines())
    assert len(hashes[0]) == len(hashes[1]) == len(names)
    changed = [name for name, raw, filtered in zip(names, *hashes, strict=True) if raw != filtered]
    assert not changed, f"Git transforms hash-bound evidence: {changed}"
