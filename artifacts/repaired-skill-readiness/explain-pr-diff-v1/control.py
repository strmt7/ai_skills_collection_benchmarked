"""Check whether a bounded diff excerpt contains a later behavioral change."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    workspace, output = args.workspace.resolve(), args.output.resolve()
    if workspace.exists() or output.exists() or output.is_relative_to(workspace) or not output.parent.is_dir():
        raise ValueError("Use a new workspace and a new output outside it")
    workspace.mkdir(parents=True)
    for side, setting, body in (
        ("before", "old", "def total(items):\n    return sum(items)\n"),
        ("after", "new", "def total(items):\n    return sum(items) + 5\n"),
    ):
        folder = workspace / side
        folder.mkdir()
        (folder / "a_settings.txt").write_text(
            "".join(f"setting_{i:04d}={setting}\n" for i in range(250)), encoding="utf-8", newline="\n"
        )
        (folder / "z_totals.py").write_text(body, encoding="utf-8", newline="\n")
    env = os.environ.copy()
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    diff = subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "diff",
            "--no-index",
            "--no-ext-diff",
            "--no-color",
            "--",
            "before",
            "after",
        ],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    version = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, encoding="utf-8", timeout=10, check=True
    ).stdout.strip()
    lines = diff.stdout.splitlines()
    head = "\n".join(lines[:200])
    checks = {
        "expected_diff_exit": diff.returncode == 1,
        "large_diff": len(lines) > 400,
        "tail_file_present": "z_totals.py" in diff.stdout,
        "tail_change_present": "+    return sum(items) + 5" in diff.stdout,
        "tail_file_missing_from_excerpt": "z_totals.py" not in head,
        "tail_change_missing_from_excerpt": "+    return sum(items) + 5" not in head,
    }
    result = {
        "schema_version": 1,
        "platform": platform.system(),
        "git_version": version,
        "diff_line_count": len(lines),
        "excerpt_line_count": 200,
        "diff_sha256": hashlib.sha256(diff.stdout.encode("utf-8")).hexdigest(),
        "diff_stderr": diff.stderr,
        "checks": checks,
        "agent_efficacy_scored": False,
        "limitations": [
            "Synthetic git diff component control; no GitHub API, posting, model, or agent-effectiveness evaluation."
        ],
    }
    with output.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({"checks": checks, "output": str(output)}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
