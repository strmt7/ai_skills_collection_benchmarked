"""Actual isolated shell exit-status controls; not a coding-agent score."""

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists; choose a new output path")
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / "tools"))
    from isolated_python import run_isolated

    code = """import subprocess
def run(request):
    commands = {
        "failed_command_piped_to_tail": "(exit 7) | tail -20",
        "failed_command_without_pipeline": "exit 7",
        "successful_command": "exit 0",
        "misleading_success_text": "printf SUCCESS; exit 9",
    }
    return {name: {"returncode": result.returncode, "stdout": result.stdout.decode()}
            for name, command in commands.items()
            for result in [subprocess.run(["/bin/sh", "-c", command], capture_output=True, timeout=2)]}
"""
    with tempfile.TemporaryDirectory(prefix="verification-pipeline-") as temporary:
        source = Path(temporary)
        (source / "candidate.py").write_text(code, encoding="utf-8")
        execution = run_isolated(source, ["candidate.py"], {}, timeout=10, output_limit=16384)
    values = execution.get("candidate_response", {}).get("result")
    expected = {
        "failed_command_piped_to_tail": {"returncode": 0, "stdout": ""},
        "failed_command_without_pipeline": {"returncode": 7, "stdout": ""},
        "successful_command": {"returncode": 0, "stdout": ""},
        "misleading_success_text": {"returncode": 9, "stdout": "SUCCESS"},
    }
    passed = values == expected and execution["status"] == "completed" and execution["cleanup_verified"]
    report = {
        "schema_version": 1,
        "evidence_class": "shell-exit-status-controls",
        "passed": bool(passed),
        "execution": execution,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Actual POSIX default-pipeline behavior and known command outcomes; no Windows pipeline equivalence, agent score or performance claim. Command status must be preserved independently of displayed tail/grep text.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": bool(passed), "observed": values}))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
