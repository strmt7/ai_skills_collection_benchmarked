#!/usr/bin/env python3
"""Fail if tracked files or branch history contain secret-shaped text.

This scanner is deliberately stricter than "real secret" detection: examples
that look like provider tokens are blocked too. Use neutral placeholders such as
<GOOGLE_API_KEY> instead of provider-shaped sample values.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES = [
    Rule("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    Rule("aws_access_key_id", re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")),
    Rule("openai_api_key", re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_]{20,}(?![A-Za-z0-9_-])")),
    Rule("github_token", re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})")),
    Rule("github_token_example_shape", re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_.-]+")),
    Rule("gitlab_token", re.compile(r"glpat-[A-Za-z0-9_-]{20,}")),
    Rule("gitlab_token_example_shape", re.compile(r"\bglpat-[A-Za-z0-9_.-]+")),
    Rule("huggingface_token", re.compile(r"hf_[A-Za-z0-9]{30,}")),
    Rule("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    Rule("slack_token_example_shape", re.compile(r"\bxox[baprs]-[A-Za-z0-9_.-]+")),
    Rule("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")),
]

SKIP_PARTS = {".git", ".pytest_cache", "__pycache__"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True)


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def tracked_files() -> list[Path]:
    return [ROOT / line for line in git("ls-files").splitlines() if line]


def history_commits() -> list[str]:
    return [line for line in git("rev-list", "HEAD").splitlines() if line]


def commit_changed_names(commit: str) -> list[str]:
    data = git_bytes("diff-tree", "-z", "--no-commit-id", "--name-only", "-r", commit)
    return [item.decode("utf-8", errors="surrogateescape") for item in data.split(b"\0") if item]


def file_text(path: Path) -> str | None:
    if SKIP_PARTS.intersection(path.parts):
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def commit_file_text(commit: str, path: str) -> str | None:
    try:
        data = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])
    except subprocess.CalledProcessError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan_text(label: str, text: str) -> list[str]:
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append(f"{label}:{line_number}: {rule.name}")
    return findings


def scan_worktree() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        text = file_text(path)
        if text is None:
            continue
        findings.extend(scan_text(path.relative_to(ROOT).as_posix(), text))
    return findings


def scan_history() -> list[str]:
    findings: list[str] = []
    for commit in history_commits():
        for name in commit_changed_names(commit):
            if not name or SKIP_PARTS.intersection(Path(name).parts):
                continue
            text = commit_file_text(commit, name)
            if text is None:
                continue
            findings.extend(scan_text(f"{commit[:12]}:{name}", text))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tracked files for secret-shaped text.")
    parser.add_argument("--history", action="store_true", help="Scan all commits reachable from local refs.")
    args = parser.parse_args()

    findings = scan_history() if args.history else scan_worktree()
    if findings:
        print("Secret-shaped text found. Replace real or example-looking values with neutral placeholders.", file=sys.stderr)
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK: no secret-shaped text found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
