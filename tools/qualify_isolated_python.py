"""Run independent Docker invocation controls or validate an existing receipt.

--check validates recorded controls and their input hashes without starting
Docker. It does not establish that the current host has been tested again.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from isolated_python import OWNER_LABEL, docker_call, run_isolated, validate_inspection

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ("tools/isolated_python.py", "tools/_isolated_worker.py", "tools/qualify_isolated_python.py")


def controls() -> list[dict[str, Any]]:
    cases = [
        ("known-good", 'def run(request):\n    return sum(request["numbers"])\n', "completed"),
        ("known-bad", "def run(request):\n    return 999\n", "completed"),
        ("missing-function", "value = 1\n", "worker_error"),
        (
            "malformed-output",
            'def run(request):\n    print("not protocol JSON", flush=True)\n    return 4\n',
            "invalid_response",
        ),
        ("nonterminating", "def run(request):\n    while True:\n        pass\n", "timeout"),
        (
            "stdout-flood",
            'import os\ndef run(request):\n    while True:\n        os.write(1, b"x" * 8192)\n',
            "output_limit",
        ),
        (
            "stderr-flood",
            'import os\ndef run(request):\n    while True:\n        os.write(2, b"x" * 8192)\n',
            "output_limit",
        ),
        (
            "leftover-child",
            "import os, time\ndef run(request):\n    if os.fork() == 0:\n        time.sleep(600)\n        os._exit(0)\n    return 4\n",
            "completed-or-timeout",
        ),
    ]
    code = """import os, socket
from pathlib import Path
def run(request):
    attempts = {}
    for name in ["/submission/candidate.py", "/worker/invoke.py", "/etc/isolation-probe"]:
        try:
            Path(name).write_text("unauthorized mutation")
            attempts[name] = "written"
        except OSError:
            attempts[name] = "denied"
    temporary = Path("/tmp/allowed.txt")
    temporary.write_text("temporary fixture")
    with socket.socket() as client:
        client.settimeout(0.5)
        try:
            client.connect(("198.51.100.1", 443))
            connected = True
        except OSError:
            connected = False
    status = Path("/proc/self/status").read_text()
    return {"uid": os.getuid(), "gid": os.getgid(), "writes": attempts,
            "temporary_write": temporary.read_text() == "temporary fixture",
            "unstaged_sentinel_visible": Path("/submission/host-sentinel.txt").exists(),
            "docker_socket_visible": Path("/var/run/docker.sock").exists(),
            "oracle_visible": Path("/oracle").exists(), "external_connection": connected,
            "no_new_privileges": "NoNewPrivs:\\t1" in status,
            "capabilities_dropped": "CapEff:\\t0000000000000000" in status}
"""
    cases.append(("filesystem-network-and-identity", code, "completed"))
    return [
        {
            "control": name,
            "code": code,
            "request": {"numbers": [2, 3, -1]} if name in {"known-good", "known-bad"} else {},
            "expected_execution_status": status,
        }
        for name, code, status in cases
    ]


def control_passes(case: dict[str, Any], result: dict[str, Any]) -> bool:
    inspection = result.get("isolation_checks")
    response = result.get("candidate_response", {})
    if not isinstance(inspection, dict) or not isinstance(response, dict):
        return False
    observed = {
        "Config": {
            "Image": inspection.get("observed_image"),
            "User": inspection.get("observed_user"),
            "Labels": {OWNER_LABEL: inspection.get("observed_ownership_token")},
        },
        "HostConfig": inspection.get("observed_host_constraints", {}),
        "Mounts": inspection.get("observed_mounts", []),
    }
    token = inspection.get("observed_ownership_token")
    if (
        not isinstance(token, str)
        or not isinstance(observed["HostConfig"], dict)
        or not isinstance(observed["Mounts"], list)
    ):
        return False
    if any(not isinstance(mount, dict) for mount in observed["Mounts"]):
        return False
    try:
        if validate_inspection(observed, token):
            return False
    except (TypeError, AttributeError):
        return False
    expected_status = case["expected_execution_status"]
    statuses = {"completed", "timeout"} if expected_status == "completed-or-timeout" else {expected_status}
    if (
        result.get("status") not in statuses
        or result.get("cleanup_verified") is not True
        or result.get("cleanup_error")
        or result.get("isolation_checks", {}).get("passed") is not True
        or result.get("isolation_checks", {}).get("errors") != []
        or result.get("scored") is not False
        or result.get("candidate_response_is_untrusted") is not True
    ):
        return False
    name = case["control"]
    candidate = response.get("result")
    if name == "known-good" or (name == "leftover-child" and result["status"] == "completed"):
        return type(candidate) is int and candidate == 4
    if name == "known-bad":
        return type(candidate) is int and candidate != 4
    if name == "filesystem-network-and-identity":
        return candidate == {
            "uid": 65534,
            "gid": 65534,
            "writes": {
                item: "denied" for item in ["/submission/candidate.py", "/worker/invoke.py", "/etc/isolation-probe"]
            },
            "temporary_write": True,
            "unstaged_sentinel_visible": False,
            "docker_socket_visible": False,
            "oracle_visible": False,
            "external_connection": False,
            "no_new_privileges": True,
            "capabilities_dropped": True,
        }
    return name not in {"stdout-flood", "stderr-flood"} or 0 < result.get("captured_bytes", 0) <= 16384


def input_hashes() -> dict[str, str]:
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in INPUTS}


def validate_receipt(report: dict[str, Any]) -> list[str]:
    errors = []
    if report.get("schema_version") != 1 or report.get("evidence_class") != "independent-container-backend-controls":
        errors.append("unsupported qualification receipt")
    if report.get("input_sha256") != input_hashes():
        errors.append("qualification source hashes changed")
    records = report.get("controls")
    if not isinstance(records, list) or len(records) != len(controls()):
        return [*errors, "incomplete control denominator"]
    for case, record in zip(controls(), records, strict=True):
        if (
            not isinstance(record, dict)
            or record.get("control") != case["control"]
            or record.get("code_sha256") != hashlib.sha256(case["code"].encode()).hexdigest()
            or record.get("expected_execution_status") != case["expected_execution_status"]
            or not isinstance(record.get("execution"), dict)
            or record.get("passed") is not True
            or not control_passes(case, record["execution"])
        ):
            errors.append(f"invalid or failed control: {case['control']}")
    if report.get("all_controls_passed") is not True:
        errors.append("qualification controls did not all pass")
    return errors


def qualify() -> dict[str, Any]:
    initial_hashes = input_hashes()
    records = []
    with tempfile.TemporaryDirectory(prefix="isolation-controls-") as temporary:
        source = Path(temporary)
        (source / "host-sentinel.txt").write_text("outside selected submission", encoding="utf-8")
        for case in controls():
            (source / "candidate.py").write_text(case["code"], encoding="utf-8")
            result = run_isolated(source, ["candidate.py"], case["request"], timeout=3, output_limit=16384)
            records.append(
                {
                    "control": case["control"],
                    "passed": control_passes(case, result),
                    "code_sha256": hashlib.sha256(case["code"].encode()).hexdigest(),
                    "expected_execution_status": case["expected_execution_status"],
                    "execution": result,
                }
            )
    engine = docker_call(["version", "--format", "{{json .Server.Version}}"])
    if input_hashes() != initial_hashes:
        raise ValueError("qualification sources changed during the observed run")
    return {
        "schema_version": 1,
        "evidence_class": "independent-container-backend-controls",
        "controls": records,
        "all_controls_passed": all(record["passed"] for record in records),
        "input_sha256": initial_hashes,
        "docker_engine_version": json.loads(engine.stdout) if engine.returncode == 0 else None,
        "scope": "Actual engine controls; no agent trials, model efficacy scores, or container escape certification. Expectations stay outside the container. Child control requires verified cleanup, allowing completion or timeout.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New receipt path, or existing receipt with --check")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    response: dict[str, Any]
    try:
        if args.check:
            report = json.loads(args.output.read_text(encoding="utf-8"))
            errors = validate_receipt(report) if isinstance(report, dict) else ["receipt must be an object"]
        else:
            if args.output.exists():
                raise ValueError("qualification receipt already exists; select a new output path")
            report = qualify()
            errors = validate_receipt(report)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(json.dumps(report, indent=2) + "\n")
        recorded_controls = report.get("controls") if isinstance(report, dict) else None
        response = {"errors": errors, "controls": len(recorded_controls) if isinstance(recorded_controls, list) else 0}
    except (OSError, ValueError, TypeError, KeyError) as exc:
        response = {"errors": [str(exc)], "controls": 0}
    print(json.dumps(response) if args.json else f"{response['controls']} controls; {len(response['errors'])} errors")
    return 1 if response["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
