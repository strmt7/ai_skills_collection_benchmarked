"""Observe the pinned syntax validator on independent YAML fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import yaml

SOURCE_SHA = "195074a331b54a7c3f1dfcea48fef90db41c549abbb32f80eea9eb142a5fa534"
CASES = {
    "ordinary_step": "steps:\n  - script: echo fixture\n",
    "bare_step": "steps:\n  - echo fixture\n",
    "bare_job": "jobs:\n  - build\n",
    "bare_stage": "stages:\n  - build\n",
    "nested_bare_step": "jobs:\n  - job: Build\n    steps:\n      - echo fixture\n",
    "conditional_mapping": "steps:\n  - ${{ if eq(parameters.run, true) }}:\n      - script: echo fixture\n",
    "step_list_insertion": "parameters:\n  - name: preBuild\n    type: stepList\n    default: []\nsteps:\n  - ${{ parameters.preBuild }}\n  - script: echo fixture\n",
    "missing_task_version": "steps:\n  - task: ExampleTask\n",
    "malformed_yaml": "steps: [\n",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validator", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.validator.read_bytes().replace(b"\r\n", b"\n")
    candidate_sha = digest(args.preflight.read_bytes().replace(b"\r\n", b"\n"))
    if digest(source) != SOURCE_SHA:
        raise ValueError("Validator source differs from the pinned bytes")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixtures = output / "fixtures"
    fixtures.mkdir()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cases = []
    for name, content in CASES.items():
        path = fixtures / f"{name}.yml"
        path.write_text(content, encoding="utf-8", newline="\n")
        if name != "malformed_yaml":
            yaml.safe_load(content)
        result = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", str(args.validator.resolve()), str(path)],
            cwd=output,
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
        )
        (output / f"{name}.stdout").write_bytes(result.stdout)
        (output / f"{name}.stderr").write_bytes(result.stderr)
        expected = 1 if name in {"missing_task_version", "malformed_yaml"} else 0
        if result.returncode != expected:
            raise ValueError(f"Unexpected validator result for {name}: {result.returncode}")
        candidate = subprocess.run(
            [sys.executable, "-I", "-X", "utf8", str(args.preflight.resolve()), str(path), "--json"],
            cwd=output,
            env=env,
            capture_output=True,
            timeout=15,
            check=False,
        )
        (output / f"{name}.preflight.stdout").write_bytes(candidate.stdout)
        (output / f"{name}.preflight.stderr").write_bytes(candidate.stderr)
        candidate_expected = {
            "ordinary_step": 0,
            "bare_step": 1,
            "bare_job": 1,
            "bare_stage": 1,
            "nested_bare_step": 1,
            "conditional_mapping": 2,
            "step_list_insertion": 2,
            "missing_task_version": 0,
            "malformed_yaml": 3,
        }[name]
        payload = json.loads(candidate.stdout)
        if candidate.returncode != candidate_expected or payload.get("azure_schema_validated") is not False:
            raise ValueError(f"Unexpected preflight result for {name}: {candidate.returncode}")
        cases.append(
            {
                "case": name,
                "fixture_sha256": digest(content.encode()),
                "exit_code": result.returncode,
                "stdout_sha256": digest(result.stdout),
                "stderr_sha256": digest(result.stderr),
                "preflight_exit_code": candidate.returncode,
                "preflight_status": payload["status"],
                "preflight_stdout_sha256": digest(candidate.stdout),
                "preflight_stderr_sha256": digest(candidate.stderr),
            }
        )
    cp_env = dict(env)
    cp_env["PYTHONIOENCODING"] = "cp1252"
    cp_env["PYTHONUTF8"] = "0"
    cp = subprocess.run(
        [sys.executable, "-X", "utf8=0", str(args.validator.resolve()), str(fixtures / "ordinary_step.yml")],
        cwd=output,
        env=cp_env,
        capture_output=True,
        timeout=15,
        check=False,
    )
    (output / "cp1252.stdout").write_bytes(cp.stdout)
    (output / "cp1252.stderr").write_bytes(cp.stderr)
    if cp.returncode == 0 or b"UnicodeEncodeError" not in cp.stderr:
        raise ValueError("Expected the explicit CP1252 output control to fail")
    cp_candidate = subprocess.run(
        [sys.executable, "-X", "utf8=0", str(args.preflight.resolve()), str(fixtures / "ordinary_step.yml"), "--json"],
        cwd=output,
        env=cp_env,
        capture_output=True,
        timeout=15,
        check=False,
    )
    (output / "cp1252.preflight.stdout").write_bytes(cp_candidate.stdout)
    (output / "cp1252.preflight.stderr").write_bytes(cp_candidate.stderr)
    if cp_candidate.returncode != 0 or json.loads(cp_candidate.stdout)["azure_schema_validated"] is not False:
        raise ValueError("Preflight failed explicit CP1252 output control")
    summary = {
        "schema_version": 1,
        "kind": "local_syntax_component_control_not_agent_benchmark",
        "source_sha256": SOURCE_SHA,
        "preflight_sha256": candidate_sha,
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "cases": cases,
        "cp1252": {
            "exit_code": cp.returncode,
            "stdout_sha256": digest(cp.stdout),
            "stderr_sha256": digest(cp.stderr),
            "unicode_encode_error": True,
            "preflight_exit_code": cp_candidate.returncode,
            "preflight_stdout_sha256": digest(cp_candidate.stdout),
            "preflight_stderr_sha256": digest(cp_candidate.stderr),
        },
        "azure_service_run": False,
        "other_validator_components_run": False,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "ok": True,
                "platform": summary["platform"],
                "cases": len(cases),
                "bare_entries_accepted": 4,
                "cp1252_exit": cp.returncode,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
