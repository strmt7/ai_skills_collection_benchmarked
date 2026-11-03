"""Check a seeded developer lock against project and build requirements."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

UV_VERSION = "0.13.7"
MINIMUM_PYTHON = "3.11.18"
ROOT = Path(__file__).resolve().parents[1]


def requirement_lines(content: str) -> list[str]:
    return [line.strip() for line in content.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def verify(
    project: Path,
    lock: Path,
    uv: str,
    resolver_source: tuple[str, ...] = ("--default-index", "https://pypi.org/simple"),
) -> dict[str, object]:
    executable = shutil.which(uv)
    if executable is None:
        raise ValueError("Required uv executable is unavailable")
    uv = str(Path(executable).resolve(strict=True))
    project = project.resolve(strict=True)
    lock = lock.resolve(strict=True)
    project_bytes = project.read_bytes()
    lock_bytes = lock.read_bytes()
    parsed = tomllib.loads(project_bytes.decode("utf-8"))
    project_data = parsed.get("project")
    build_data = parsed.get("build-system")
    tool_data = parsed.get("tool", {})
    if not isinstance(project_data, dict) or not isinstance(build_data, dict) or not isinstance(tool_data, dict):
        raise ValueError("project, build-system and tool sections must be tables")
    uv_data = tool_data.get("uv", {})
    if not isinstance(uv_data, dict) or uv_data:
        raise ValueError("custom uv project settings require a separately qualified lock")
    dynamic = project_data.get("dynamic", [])
    if not isinstance(dynamic, list) or dynamic:
        raise ValueError("dynamic project metadata is unsupported")
    requirements = build_data.get("requires")
    extras = project_data.get("optional-dependencies")
    groups = [project_data.get("dependencies"), requirements]
    if not isinstance(extras, dict):
        raise ValueError("test and lint dependency groups are required")
    groups.extend([extras.get("test"), extras.get("lint")])
    if any(not isinstance(group, list) or any(not isinstance(v, str) or "@" in v for v in group) for group in groups):
        raise ValueError("dependency groups must be lists of registry requirement strings")
    if not requirements:
        raise ValueError("build-system.requires must not be empty")
    lock_text = lock_bytes.decode("utf-8")
    for line in requirement_lines(lock_text):
        if line.startswith("--"):
            if not re.fullmatch(r"--hash=sha256:[0-9a-f]{64}(?: \\)?", line):
                raise ValueError("lock contains a noncanonical hash or option")
        elif "--" in line or " @ " in line:
            raise ValueError("lock contains an inline option or direct reference")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith(("UV_", "PIP_", "CONDA_"))
        and key.upper() not in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
    }
    version = subprocess.run(
        [uv, "--version"], capture_output=True, text=True, timeout=30, check=False, env=environment
    )
    if version.returncode or version.stdout.split()[:2] != ["uv", UV_VERSION]:
        raise ValueError("Required uv " + UV_VERSION + " is unavailable")
    with tempfile.TemporaryDirectory(prefix="skills-dev-lock-") as directory:
        temp = Path(directory)
        frozen_project = temp / "pyproject.toml"
        frozen_project.write_bytes(project_bytes)
        build_input = temp / "build.in"
        build_input.write_text("\n".join(requirements) + "\n", encoding="utf-8", newline="\n")
        candidate = temp / "candidate.lock"
        seed_lines = []
        for line in lock_text.splitlines():
            if line.lstrip().startswith("--hash=sha256:"):
                continue
            seed_lines.append(line.rstrip().removesuffix("\\").rstrip())
        candidate.write_text("\n".join(seed_lines) + "\n", encoding="utf-8", newline="\n")
        args = [
            uv,
            "pip",
            "compile",
            str(frozen_project),
            str(build_input),
            "--extra",
            "test",
            "--extra",
            "lint",
            "--universal",
            "--python-version",
            MINIMUM_PYTHON,
            "--generate-hashes",
            "--no-strip-markers",
            "--only-binary=:all:",
            "--no-annotate",
            "--no-header",
            "--no-config",
            *resolver_source,
            "--cache-dir",
            str(temp / "cache"),
            "--output-file",
            str(candidate),
            "--quiet",
        ]
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
            check=False,
            cwd=project.parent,
            env=environment,
        )
        if result.returncode:
            return {"valid": False, "errors": ["uv resolution failed"], "diagnostic": result.stderr[-3000:]}
        same = requirement_lines(lock_bytes.decode("utf-8")) == requirement_lines(candidate.read_text(encoding="utf-8"))
        if project.read_bytes() != project_bytes or lock.read_bytes() != lock_bytes:
            raise ValueError("project or lock changed during verification")
    return {
        "valid": same,
        "errors": [] if same else ["lock differs from the seeded project resolution"],
        "project_sha256": hashlib.sha256(project_bytes).hexdigest(),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "uv_version": UV_VERSION,
        "minimum_python": MINIMUM_PYTHON,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT / "pyproject.toml")
    parser.add_argument("--lock", type=Path, default=ROOT / "requirements-dev-lock.txt")
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify(args.project, args.lock, args.uv)
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired) as exc:
        result = {"valid": False, "errors": [str(exc)]}
    print(json.dumps(result, sort_keys=True) if args.json else result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
