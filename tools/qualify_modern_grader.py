"""Qualify the modern confined grader without claiming agent performance."""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

import appcontainer_dependencies as dependencies
import appcontainer_runtime as runtime
import grade_agent_submission as gateway
import grade_validator_appcontainer_modern as modern
from _windows_appcontainer import checked_path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "artifacts/agent-trials/development-v2/repetition-1/default/submission"


def qualify(runtime_home: Path, dependency_home: Path, output: Path, revision: str) -> dict[str, Any]:
    runtime_home, dependency_home, output = (checked_path(path) for path in (runtime_home, dependency_home, output))
    modern.checked_homes(runtime_home, dependency_home, output)
    output.mkdir(parents=True, exist_ok=False)
    qualifier_hash = runtime.digest(Path(__file__))
    common: dict[str, Any] = {
        "fixture": ROOT,
        "revision": revision,
        "runtime_home": runtime_home,
        "dependency_home": dependency_home,
    }
    reference = gateway.evaluate(gateway.GRADER, REFERENCE, output=output / "reference", **common)
    current = gateway.evaluate(gateway.GRADER, ROOT, output=output / "current", **common)
    for result in (reference, current):
        if (result.get("status"), result.get("checks_passed"), result.get("checks_total")) != ("task_passed", 17, 17):
            raise ValueError("A legitimate validator did not pass the confined controls")

    submission = output / "attacker"
    (submission / "tools").mkdir(parents=True)
    marker = output / "controller-marker.txt"
    marker.write_text("controller-owned", encoding="utf-8")
    protected_dependency = dependency_home / "runtime/jsonschema/__init__.py"
    before = runtime.digest(protected_dependency)
    source = (
        "from pathlib import Path\nchecks=[]\ntry:\n"
        f" Path({str(marker)!r}).write_text('changed')\n"
        " checks.append('marker-write-allowed')\nexcept OSError: checks.append('marker-write-denied')\ntry:\n"
        f" checks.append('marker-read:'+Path({str(marker)!r}).read_text())\n"
        "except OSError: checks.append('marker-read-denied')\ntry:\n"
        f" Path({str(protected_dependency)!r}).write_text('changed')\n"
        " checks.append('dependency-write-allowed')\nexcept OSError: checks.append('dependency-write-denied')\n"
        "def validate_artifact(path):\n"
        " return {'verdict':'artifact_incomplete','errors':checks,'warnings':[]}\n"
    )
    (submission / "tools/check_benchmark_artifact.py").write_text(source, encoding="utf-8")
    attack = gateway.evaluate(gateway.GRADER, submission, output=output / "attack", **common)
    denied = {"marker-write-denied", "marker-read-denied", "dependency-write-denied"}
    checks = attack.get("checks")
    if (
        not isinstance(checks, list)
        or len(checks) != 17
        or attack.get("status") != "task_failed"
        or attack.get("checks_passed") != 15
        or attack.get("checks_total") != 17
        or marker.read_text(encoding="utf-8") != "controller-owned"
        or runtime.digest(protected_dependency) != before
        or any(set(check["response"].get("value", {}).get("errors", [])) != denied for check in checks)
    ):
        raise ValueError("A candidate escaped the boundary or an attack control failed")
    specification = dependencies.load_specification()
    bundle = dependency_home / "dependencies.zip"
    if runtime.digest(bundle) != specification["archive_sha256"]:
        raise ValueError("Installed dependency bundle changed")
    archives = output / "tamper-archives"
    archives.mkdir()
    with zipfile.ZipFile(bundle) as package:
        expected_names = {item["filename"] for item in specification["packages"]}
        if set(package.namelist()) != expected_names or len(package.namelist()) != len(expected_names):
            raise ValueError("Installed dependency bundle contents differ from their pins")
        for name in expected_names:
            if not isinstance(name, str) or Path(name).name != name or ":" in name or "\\" in name:
                raise ValueError("Installed dependency bundle contains an unsafe archive name")
            if package.getinfo(name).file_size > dependencies.MAX_ARCHIVE:
                raise ValueError("Installed dependency archive exceeds its byte budget")
            (archives / name).write_bytes(package.read(name))
    tampered_home = output / "tampered-dependencies"
    dependencies.install_archives(tampered_home, specification, archives)
    (tampered_home / "runtime/jsonschema/__init__.py").write_text("tampered\n", encoding="utf-8")
    rejected_output = output / "tampered-run"
    rejected = gateway.evaluate(
        gateway.GRADER,
        submission,
        fixture=ROOT,
        revision=revision,
        runtime_home=runtime_home,
        dependency_home=tampered_home,
        output=rejected_output,
    )
    if (
        rejected.get("status") != "harness_error"
        or rejected_output.exists()
        or marker.read_text(encoding="utf-8") != "controller-owned"
    ):
        raise ValueError("Changed dependencies were not rejected before candidate execution")
    if runtime.digest(Path(__file__)) != qualifier_hash:
        raise ValueError("Qualification source changed during execution")
    result = {
        "ok": True,
        "qualifier_sha256": qualifier_hash,
        "dependency_bundle_sha256": reference["dependency_bundle_sha256"],
        "reference_checks": 17,
        "current_checks": 17,
        "attack_checks": attack["checks_total"],
        "controller_marker_unchanged": True,
        "dependency_unchanged": True,
        "tampered_dependencies_rejected_before_execution": True,
        "fixture_commit": revision,
        "agent_performance_claim": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-home", type=Path, required=True)
    parser.add_argument("--dependency-home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = qualify(args.runtime_home, args.dependency_home, args.output, args.revision)
    except (OSError, ValueError, RuntimeError) as error:
        result = {"ok": False, "errors": [str(error)], "agent_performance_claim": False}
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
