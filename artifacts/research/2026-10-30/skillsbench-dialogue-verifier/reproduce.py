"""Exercise the pinned dialogue verifier against an output-only fixture on Linux."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import tempfile
from pathlib import Path

INPUTS = {
    "verifier": "d0effcfa8ba898260bce69ba8a0c4852f4959a83e9130cc69c13847f0f05b01c",
    "script": "f63dcc28386cb2f963362eb78d40af75eb362945646c3c86e2a699bb2f14b409",
    "oracle": "7c26e8db8b9624f73d3f0ee6406a5eda0a2044ed401efbb98d9eff8092a57f15",
}
DOT = "digraph G { Start -> End; x [shape=diamond]; }\n"


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def run_case(python: str, root: Path, verifier: bytes, script: bytes, graph: dict, dot: str) -> dict[str, object]:
    root.mkdir()
    (root / "test_upstream.py").write_bytes(verifier)
    (root / "script.txt").write_bytes(script)
    (root / "dialogue.json").write_bytes((json.dumps(graph, ensure_ascii=False, indent=2) + "\n").encode())
    (root / "dialogue.dot").write_text(dot, encoding="utf-8")
    if (root / "solution.py").exists():
        raise AssertionError("The output-only fixture unexpectedly contains a parser")
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    run = subprocess.run(
        [python, "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_upstream.py"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    passed = re.search(r"(\d+) passed", run.stdout)
    failed = re.search(r"(\d+) failed", run.stdout)
    skipped = re.search(r"(\d+) skipped", run.stdout)
    errors = re.search(r"(\d+) errors?", run.stdout)
    if (root / "solution.py").exists():
        raise AssertionError("The verifier unexpectedly created a parser")
    return {
        "pytest_exit": run.returncode,
        "passed": int(passed.group(1)) if passed else 0,
        "failed": int(failed.group(1)) if failed else 0,
        "skipped": int(skipped.group(1)) if skipped else 0,
        "errors": int(errors.group(1)) if errors else 0,
        "failing_tests": re.findall(r"^FAILED test_upstream\.py::(\S+)", run.stdout, re.MULTILINE),
        "solution_present": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--python", required=True)
    args = parser.parse_args()
    if platform.system() != "Linux":
        raise ValueError("This control is qualified only on Linux")
    for path in (
        Path("/app/dialogue.json"),
        Path("/app/dialogue.dot"),
        Path("/app/script.txt"),
        Path("/app/solution.py"),
    ):
        if path.exists():
            raise ValueError("Absolute upstream fixture paths must be absent for this control")
    data = {name: pinned(getattr(args, name), sha) for name, sha in INPUTS.items()}
    info = json.loads(
        subprocess.check_output(
            [
                args.python,
                "-c",
                "import json,pytest,sys; print(json.dumps({'pytest':pytest.__version__,'python':sys.version.split()[0]}))",
            ],
            text=True,
        )
    )
    if info["pytest"] != "8.3.4":
        raise ValueError("The control requires pytest 8.3.4")
    original = json.loads(data["oracle"])
    normalized = json.loads(data["oracle"])
    missing = sum("text" not in edge for edge in normalized["edges"])
    for edge in normalized["edges"]:
        if "text" not in edge:
            edge["text"] = ""
    if missing != 146:
        raise ValueError("The pinned oracle schema changed")
    if any(edge["from"] == "Start" and edge["to"] == "End" for edge in normalized["edges"]):
        raise ValueError("The intentionally unrelated DOT edge is present in the graph")
    temp_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="skillsbench-dialogue-control-", dir=temp_root) as tmp:
        root = Path(tmp).resolve()
        if not root.is_relative_to(temp_root):
            raise ValueError("Unexpected temporary path")
        cases = {
            "original_oracle": run_case(
                args.python, root / "original", data["verifier"], data["script"], original, DOT
            ),
            "normalized_output_only": run_case(
                args.python, root / "normalized", data["verifier"], data["script"], normalized, DOT
            ),
            "invalid_dot": run_case(
                args.python, root / "invalid", data["verifier"], data["script"], normalized, "not a graph\n"
            ),
        }
    expected_original = {
        "pytest_exit": 1,
        "passed": 34,
        "failed": 1,
        "skipped": 0,
        "errors": 0,
        "failing_tests": ["test_system_basics[schema_validation]"],
        "solution_present": False,
    }
    expected_normalized = {
        "pytest_exit": 0,
        "passed": 35,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "failing_tests": [],
        "solution_present": False,
    }
    expected_invalid = {
        "pytest_exit": 1,
        "passed": 31,
        "failed": 4,
        "skipped": 0,
        "errors": 0,
        "failing_tests": [f"test_visualization_validity[{name}]" for name in ("header", "syntax", "shapes", "content")],
        "solution_present": False,
    }
    if cases != {
        "original_oracle": expected_original,
        "normalized_output_only": expected_normalized,
        "invalid_dot": expected_invalid,
    }:
        raise AssertionError(f"Upstream verifier outcomes changed: {cases}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "control_python": platform.python_version(),
                "pytest_python": info["python"],
                "pytest": info["pytest"],
                "input_sha256": INPUTS,
                "nodes": len(original["nodes"]),
                "edges": len(original["edges"]),
                "missing_edge_text_fields": missing,
                "dot_edges": 1,
                "dot_edge_present_in_graph": False,
                "benchmark_runner_executed": False,
                "model_scored": False,
                "cases": cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
