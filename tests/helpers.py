import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import check_benchmark_artifact

MIN_SCENARIOS = 3


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def complete_artifacts():
    artifact_root = ROOT / "artifacts" / "benchmark-runs"
    if not artifact_root.exists():
        return []
    artifacts = []
    for path in sorted(artifact_root.rglob("artifact.json")):
        result = check_benchmark_artifact.validate_artifact(path)
        assert result["verdict"] == "artifact_complete", (path, result)
        artifacts.append((path, json.loads(path.read_text(encoding="utf-8")), result))
    return artifacts


def assert_unique(items, key):
    values = [item[key] for item in items]
    assert len(values) == len(set(values))
    return values
