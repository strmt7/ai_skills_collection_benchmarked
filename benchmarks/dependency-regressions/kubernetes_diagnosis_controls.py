"""Qualify unchanged diagnostic-script boundaries with offline command spies."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
EXPECTED = {
    "original_helper_completes_against_owned_command_spy",
    "warning_events_permission_failure_aborts_snapshot",
    "redis_permission_failure_is_misreported_as_missing_pod",
    "metrics_permission_failure_is_misreported_as_unavailable_server",
    "helper_requests_have_no_explicit_api_timeout",
    "namespace_override_is_used_except_cluster_scoped_node_metrics",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    from build_catalog import sanitized_file_bytes
    from isolated_python import run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt must be new")
    inputs = {
        "original-diagnose.sh": ROOT
        / "included/skills/by-category/testing-qa-benchmarking/security-reference/debug-buttercup/scripts/diagnose.sh",
        "candidate.py": Path(__file__).with_name("kubernetes_diagnosis_fixture.py"),
    }
    hashes = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs.values()
    }
    with tempfile.TemporaryDirectory(prefix="diagnosis-controls-") as temporary:
        stage = Path(temporary)
        for name, path in inputs.items():
            if name == "original-diagnose.sh":
                (stage / name).write_bytes(sanitized_file_bytes(path))
            else:
                shutil.copyfile(path, stage / name)
        staged_script_sha256 = hashlib.sha256((stage / "original-diagnose.sh").read_bytes()).hexdigest()
        invocation = run_isolated(stage, list(inputs), {}, timeout=30)
    result = invocation.get("candidate_response", {}).get("result", {})
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and set(result.get("checks", [])) == EXPECTED
        and len(result.get("checks", [])) == len(EXPECTED)
        and result.get("temporary_directory_removed") is True
        and result.get("uid") == 65534
        and result.get("cluster_contacted") is False
        and result.get("agent_processes") == 0
    )
    if any(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest for path, digest in hashes.items()):
        raise ValueError("source changed during controls")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-original-kubernetes-diagnostic-helper-command-spy-controls",
        "passed": passed,
        "project_file_sha256": hashes,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "staged_script_canonical_sha256": staged_script_sha256,
        "fixture_adaptations": [
            "Apply existing canonical LF policy to the private script copy",
            "Inject an owned Bash function invoking a Python command spy; /tmp remains noexec",
        ],
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "scope": "Source-grounded helper contracts with owned kubectl spies; no cluster, live authorization or coding-agent score",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "status": invocation["status"],
                "checks": result.get("checks", []),
                "cleanup_verified": invocation["cleanup_verified"],
            }
        )
    )
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
