"""Observe selected Bash error-handling behavior independently of an agent."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[3]
GUIDE = (
    ROOT
    / "included/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator/docs/bash-scripting-guide.md"
)
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator/SKILL.md"
)
SCRIPTS = {
    "standalone": "set -e\nf() { false; printf 'continued\\n'; }\nf\nprintf 'after\\n'\n",
    "conditional": "set -e\nf() { false; printf 'continued\\n'; }\nif f; then printf 'branch\\n'; fi\n",
    "explicit": "set -e\nf() { false || return; printf 'continued\\n'; }\nif f; then printf 'branch\\n'; else printf 'caught\\n'; fi\n",
    "pipeline": (
        "set -o pipefail\n"
        "{ sleep 0.25; printf 'left\\n' >&2; exit 7; } | { printf 'right\\n' >&2; exit 4; }\n"
        "printf 'status=%s\\n' \"$?\"\n"
    ),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def check(bash: Path) -> dict[str, object]:
    cases = {}
    for name, script in SCRIPTS.items():
        result = subprocess.run(
            [str(bash), "-c", script], capture_output=True, text=True, encoding="utf-8", timeout=20, check=False
        )
        cases[name] = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    version = subprocess.run(
        [str(bash), "--version"], capture_output=True, text=True, encoding="utf-8", timeout=20, check=True
    ).stdout.splitlines()[0]
    observations = {
        "standalone_stopped": cases["standalone"]["exit_code"] != 0 and cases["standalone"]["stdout"] == "",
        "conditional_continued": cases["conditional"]["exit_code"] == 0
        and cases["conditional"]["stdout"] == "continued\nbranch\n",
        "explicit_propagation": cases["explicit"]["exit_code"] == 0 and cases["explicit"]["stdout"] == "caught\n",
        "pipeline_status": cases["pipeline"]["exit_code"] == 0 and cases["pipeline"]["stdout"] == "status=4\n",
    }
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "bash_version": version,
        "bash_executable_sha256": hashlib.sha256(bash.read_bytes()).hexdigest(),
        "source_guide_sha256": sha(GUIDE),
        "overlay_skill_sha256": sha(OVERLAY),
        "cases": cases,
        "observations_match": observations,
        "agent_efficacy_scored": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bash", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(args.bash.resolve(strict=True))
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0 if all(cast(dict[str, bool], result["observations_match"]).values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
