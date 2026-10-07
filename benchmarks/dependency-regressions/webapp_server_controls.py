#!/usr/bin/env python3
"""Replay unchanged server-helper findings in the qualified Linux backend."""

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
SOURCE = "included/skills/by-category/testing-qa-benchmarking/official-reference/webapp-testing/scripts/with_server.py"
EXPECTED = {
    "unrelated_open_port_accepts_failed_server",
    "client_failure_status_is_preserved",
    "undrained_server_output_blocks_readiness",
    "shell_child_survives_helper_cleanup",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New receipt; never overwritten")
    return parser


def main(argv=None):
    from isolated_python import run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    fixture = Path(__file__).with_name("webapp_server_fixture.py")
    hashes = {
        SOURCE: hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest(),
        fixture.relative_to(ROOT).as_posix(): hashlib.sha256(fixture.read_bytes()).hexdigest(),
    }
    with tempfile.TemporaryDirectory(prefix="webapp-server-") as temporary:
        stage = Path(temporary)
        shutil.copy2(ROOT / SOURCE, stage / "with_server.py")
        shutil.copy2(fixture, stage / "candidate.py")
        invocation = run_isolated(stage, ["with_server.py", "candidate.py"], {}, timeout=25)
    result = invocation.get("candidate_response", {}).get("result", {})
    controls = result.get("controls", [])
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and result.get("platform") == "linux"
        and result.get("uid") == 65534
        and len(controls) == len(EXPECTED)
        and {c["control"] for c in controls} == EXPECTED
        and all(c.get("passed") is True for c in controls)
    )
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"input changed: {name}")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-webapp-server-helper-contract-controls",
        "passed": passed,
        "project_file_sha256": hashes,
        "invocation": invocation,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "agent_efficacy_scored": False,
        "source_implementation_repaired": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "status": invocation["status"],
                "controls": controls,
                "cleanup_verified": invocation["cleanup_verified"],
            }
        )
    )
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())
