"""Run a bounded, fail-closed Gitleaks scan of a complete local Git history."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 900
OUTPUT_LIMIT = 16 * 1024 * 1024


class GateError(ValueError):
    """A safely reportable history scan failure."""


def _supervisor():
    """Load the source-bound process supervisor in isolated Python mode."""
    root = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root)
    try:
        import _bounded_process as bounded
    finally:
        sys.path.pop(0)
    return bounded


def _command(gitleaks: Path, git: Path, repository: Path, expected_sha256: str) -> list[str]:
    """Select only the repository-owned worker and explicit executables."""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise GateError("Provide the approved lowercase Gitleaks SHA-256")
    if not all(path.is_absolute() for path in (gitleaks, git, repository)):
        raise GateError("Gitleaks, Git and repository paths must be absolute")
    root = Path(__file__).resolve().parent
    worker = root / "_gitleaks_history_worker.py"
    leader = root / "_bounded_worker_leader.py"
    executable = Path(sys.executable)
    if not executable.is_absolute() or not executable.is_file() or not worker.is_file():
        raise GateError("History scan worker is unavailable")
    command = [str(executable), "-I", "-S", str(worker if sys.platform == "win32" else leader)]
    if sys.platform != "win32":
        if not leader.is_file():
            raise GateError("History scan process supervisor is unavailable")
        command.append(worker.name)
    return [*command, str(gitleaks), str(git), str(repository), expected_sha256]


def _run(command: list[str]) -> dict[str, Any]:
    """Supervise the scanner and its descendants with bounded output and time."""
    bounded = _supervisor()
    try:
        if sys.platform == "win32":
            return bounded.run_windows(command, TIMEOUT, OUTPUT_LIMIT)
        return bounded.run_posix(command, TIMEOUT, OUTPUT_LIMIT)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        raise GateError("History scan worker could not be supervised") from error


def _diagnostics(path: Path, repository: Path, raw: bytes) -> None:
    """Retain diagnostics only at a new, explicitly selected private location."""
    root_dir = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root_dir)
    try:
        from _windows_appcontainer import checked_path
    finally:
        sys.path.pop(0)
    destination = checked_path(path)
    root = repository.resolve()
    if destination.is_relative_to(root) and not destination.is_relative_to(root / ".venv"):
        raise GateError("Place diagnostics outside the repository or under its .venv")
    try:
        fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            stream = os.fdopen(fd, "wb")
        except BaseException:
            os.close(fd)
            raise
        with stream:
            stream.write(raw)
    except OSError as error:
        raise GateError("Could not retain scanner diagnostics") from error


def _finding_result(output: bytes, decoded: str, count: int, status: int) -> dict[str, Any]:
    """Require the reported finding count to match the retained redacted output."""
    observed = sum(1 for _ in re.finditer(rb"(?m)^Finding:", output))
    if observed != count:
        return {
            "passed": False,
            "reason": "incomplete_finding_output",
            "findings": count,
            "observed_findings": observed,
            "redacted_output": decoded,
        }
    return {
        "passed": False,
        "reason": "findings",
        "findings": count,
        "exit_code": status,
        "redacted_output": decoded,
    }


def _diagnostic_result(stderr: bytes, decoded: str, retained: bool) -> dict[str, Any]:
    """Summarize unexpected diagnostics without exposing potentially sensitive bytes."""
    result = {
        "passed": False,
        "reason": "scanner_diagnostics",
        "diagnostic_bytes": len(stderr),
        "diagnostic_sha256": hashlib.sha256(stderr).hexdigest(),
        "diagnostics_retained": retained,
        "redacted_output": decoded,
    }
    if stderr.rstrip(b"\r\n") == b"Repository contains a Gitleaks ignore file":
        result["error"] = "Repository contains a Gitleaks ignore file"
    return result


def evaluate(result: dict[str, Any], repository: Path, diagnostics: Path | None) -> dict[str, Any]:
    """Reject incomplete scans and retain redacted findings without suppressions."""
    stderr = result["stderr"]
    output = result["stdout"]
    try:
        decoded = output.decode("utf-8")
    except UnicodeDecodeError:
        if diagnostics is not None:
            _diagnostics(diagnostics, repository, output)
        return {
            "passed": False,
            "reason": "invalid_output_encoding",
            "output_bytes": len(output),
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "diagnostics_retained": diagnostics is not None,
        }
    reason = result["termination_reason"]
    status = result["exit_code"]
    summary = re.fullmatch(rb"[0-9]{1,2}:[0-9]{2}(?:AM|PM) WRN leaks found: ([1-9][0-9]*)\r?\n", stderr)
    expected_findings = status == 1 and summary is not None
    if stderr and not expected_findings and diagnostics is not None:
        _diagnostics(diagnostics, repository, stderr)
    if reason is not None:
        return {
            "passed": False,
            "reason": "scan_incomplete",
            "termination_reason": reason,
            "redacted_output": decoded,
        }
    if stderr and not expected_findings:
        return _diagnostic_result(stderr, decoded, diagnostics is not None)
    if status == 1 and summary is not None:
        return _finding_result(output, decoded, int(summary.group(1)), status)
    if status != 0 or output:
        return {
            "passed": False,
            "reason": "scanner_failed",
            "exit_code": status,
            "redacted_output": decoded,
        }
    return {"passed": True, "reason": "clean", "exit_code": 0, "redacted_output": ""}


def build_parser() -> argparse.ArgumentParser:
    """Define the explicit scanner, trusted Git and optional diagnostics paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gitleaks", required=True, type=Path)
    parser.add_argument("--gitleaks-sha256", required=True)
    parser.add_argument("--git", required=True, type=Path)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--diagnostics", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the fail-closed history gate and emit its result."""
    args = build_parser().parse_args(argv)
    try:
        command = _command(args.gitleaks, args.git, args.repository, args.gitleaks_sha256)
        result = evaluate(_run(command), args.repository, args.diagnostics)
    except GateError as error:
        result = {"passed": False, "reason": "invalid_or_unavailable_scan", "error": str(error)}
    except (OSError, ValueError):
        result = {"passed": False, "reason": "invalid_or_unavailable_scan"}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        if result.get("redacted_output"):
            print(result["redacted_output"], end="")
        print("Gitleaks history scan: " + result["reason"], file=sys.stderr)
        if result.get("error"):
            print(result["error"], file=sys.stderr)
        if result.get("termination_reason"):
            print("Worker termination: " + result["termination_reason"], file=sys.stderr)
        if result.get("diagnostic_sha256"):
            disposition = "retained locally" if result["diagnostics_retained"] else "withheld; use --diagnostics"
            print("Error diagnostics " + disposition + "; SHA-256: " + result["diagnostic_sha256"], file=sys.stderr)
    if result["passed"]:
        return 0
    return 1 if result["reason"] == "findings" else 2


if __name__ == "__main__":
    raise SystemExit(main())
