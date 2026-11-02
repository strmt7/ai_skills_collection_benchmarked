"""Reproduce selected shell-generator defects without running an agent."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "included/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator"
OVERLAY = (
    ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator"
)


def canonical(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(command: list[str]) -> int:
    return subprocess.run(command, capture_output=True, timeout=120, check=False).returncode


def check(bash: Path, dash: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="shell-generator-control-") as temporary:
        scratch = Path(temporary)
        source = scratch / "source with spaces"
        shutil.copytree(SOURCE, source)
        for path in source.rglob("*.sh"):
            path.write_bytes(canonical(path))

        invalid = scratch / "generated output with spaces.sh"
        invalid.write_bytes(b"#!/usr/bin/env bash\nif then\n")
        valid = scratch / "valid portable output.sh"
        valid.write_bytes(b"#!/bin/sh\nprintf '%s\\n' 'control'\n")
        template = source / "assets/templates/standard-template.sh"
        checks = {
            "upstream_self_checks": run(
                [str(bash), str(source / "scripts/run_ci_checks.sh"), "--skip-shellcheck", "--skip-regression-tests"]
            ),
            "invalid_output_bash_syntax": run([str(bash), "-n", str(invalid)]),
            "valid_output_bash_syntax": run([str(bash), "-n", str(valid)]),
            "valid_output_dash_syntax": run([str(dash), "-n", str(valid)]),
            "valid_output_dash_execution": run([str(dash), str(valid)]),
            "template_bash_syntax": run([str(bash), "-n", str(template)]),
            "template_dash_syntax": run([str(dash), "-n", str(template)]),
        }
        expected = {
            "upstream_self_checks": checks["upstream_self_checks"] == 0,
            "invalid_output_rejected": checks["invalid_output_bash_syntax"] != 0,
            "valid_output_accepted": all(
                checks[key] == 0
                for key in ("valid_output_bash_syntax", "valid_output_dash_syntax", "valid_output_dash_execution")
            ),
            "template_shell_difference": checks["template_bash_syntax"] == 0 and checks["template_dash_syntax"] != 0,
        }
        return {
            "schema_version": 1,
            "platform": platform.system(),
            "source_skill_sha256": digest(canonical(SOURCE / "SKILL.md")),
            "source_ci_sha256": digest(canonical(SOURCE / "scripts/run_ci_checks.sh")),
            "source_template_sha256": digest(canonical(SOURCE / "assets/templates/standard-template.sh")),
            "overlay_skill_sha256": digest(canonical(OVERLAY / "SKILL.md")),
            "bash_executable_sha256": digest(bash.read_bytes()),
            "dash_executable_sha256": digest(dash.read_bytes()),
            "exit_codes": checks,
            "observations_match": expected,
            "agent_efficacy_scored": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", required=True, type=Path)
    parser.add_argument("--dash", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.bash.resolve(strict=True), args.dash.resolve(strict=True))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0 if all(cast(dict[str, bool], result["observations_match"]).values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
