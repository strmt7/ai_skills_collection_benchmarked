#!/usr/bin/env python3
"""Fail if tracked files or branch history contain secret-shaped text.

This scanner is deliberately stricter than "real secret" detection: example
values that *look like* provider tokens are blocked too. Use neutral
placeholders such as ``<GOOGLE_API_KEY>`` instead of provider-shaped sample
values.

Two layers of detection are applied:

1. A curated regex catalog inspired by detect-secrets, gitleaks and
   trufflehog pattern libraries. Provider-specific rules are paired with
   "example_shape" rules so that obvious provider-shaped placeholders are
   flagged before they land in public history.
2. An entropy heuristic that flags long opaque ``key=VALUE`` / ``token:VALUE``
   assignments whose Shannon entropy exceeds the conventional thresholds used
   by detect-secrets (>3 bits/char for hex-only strings, >4.5 for
   base64-class strings). The heuristic requires both a credential-like
   variable name *and* a high-entropy value to keep false positives low.

CLI:

    python3 tools/check_no_secret_patterns.py           # scan worktree
    python3 tools/check_no_secret_patterns.py --history # scan all commits

Exit code 0 means clean, 1 means at least one finding.
"""

from __future__ import annotations

import argparse
import math
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


# Provider regexes kept identical to the previous implementation so we do not
# weaken detection. Each "example_shape" rule is deliberately broad: it will
# match obvious provider-shaped placeholders (see provider name prefixes below).
RULES: list[Rule] = [
    Rule("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    Rule(
        "aws_access_key_id",
        re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
    ),
    Rule(
        "openai_api_key",
        re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_]{20,}(?![A-Za-z0-9_-])"),
    ),
    Rule(
        "provider_api_key_example_shape",
        re.compile(
            r"(?<![A-Za-z0-9_-])sk-(?:proj-)?"
            r"(?:[xX][xX-]{2,}|\.{3}|[A-Za-z0-9][A-Za-z0-9_.-]*\.{3})"
            r"(?![A-Za-z0-9_-])"
        ),
    ),
    Rule(
        "github_token",
        re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})"),
    ),
    Rule(
        "github_token_example_shape",
        re.compile(r"\b(?:gh[pousr]_|github_pat_)[A-Za-z0-9_.-]+"),
    ),
    Rule("gitlab_token", re.compile(r"glpat-[A-Za-z0-9_-]{20,}")),
    Rule("gitlab_token_example_shape", re.compile(r"\bglpat-[A-Za-z0-9_.-]+")),
    Rule("huggingface_token", re.compile(r"hf_[A-Za-z0-9]{30,}")),
    Rule("slack_token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    Rule("slack_token_example_shape", re.compile(r"\bxox[baprs]-[A-Za-z0-9_.-]+")),
    Rule("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")),
]


# Entropy heuristic configuration. Triggers only when the line already contains
# a credential-like variable name, so that README prose and JSON blobs do not
# false-positive on unrelated high-entropy strings (e.g. git commit SHAs,
# content hashes). Tuned against the scanner's own fixtures.
ENTROPY_NAME_PATTERN = re.compile(
    r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?key|access[_-]?token"
    r"|auth[_-]?token|bearer[_-]?token|client[_-]?secret|private[_-]?key"
    r"|password|passwd|pwd)\b"
)
# Match assignments of the form key=VALUE, key: VALUE, key: 'VALUE', key = "VALUE".
ENTROPY_ASSIGNMENT_PATTERN = re.compile(
    r"""(?xi)
    (?:api[_-]?key|secret[_-]?key|access[_-]?key|access[_-]?token
       |auth[_-]?token|bearer[_-]?token|client[_-]?secret|password|passwd|pwd)
    \s*[:=]\s*
    (?:['"])?
    (?P<value>[A-Za-z0-9_+/=.\-]{24,200})
    (?:['"])?
    """
)

HEX_CHARSET = set("0123456789abcdefABCDEF")
BASE64_CHARSET = set(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
)

# detect-secrets / trufflehog defaults: > 3.0 for hex, > 4.5 for base64.
HEX_ENTROPY_THRESHOLD = 3.0
BASE64_ENTROPY_THRESHOLD = 4.5

# Obvious placeholder values that must not trip the entropy heuristic.
PLACEHOLDER_VALUES = {
    "changeme",
    "example",
    "placeholder",
    "redacted",
    "xxxxxxxx",
    "your_api_key",
    "your-api-key",
}


SKIP_PARTS = {".git", ".pytest_cache", "__pycache__"}


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    length = len(value)
    counts: dict[str, int] = {}
    for char in value:
        counts[char] = counts.get(char, 0) + 1
    return -sum(
        (count / length) * math.log2(count / length) for count in counts.values()
    )


def _entropy_findings(line: str) -> list[str]:
    """Return rule names if the line looks like a credential assignment."""
    findings: list[str] = []
    if not ENTROPY_NAME_PATTERN.search(line):
        return findings
    for match in ENTROPY_ASSIGNMENT_PATTERN.finditer(line):
        value = match.group("value")
        lowered = value.lower().strip("\"' ")
        if lowered in PLACEHOLDER_VALUES or lowered.startswith("<") or lowered.startswith("${"):
            continue
        # Ignore obviously structured tokens like URLs and filesystem paths.
        if "/" in value and any(c in value for c in (":", "@")):
            continue
        entropy = shannon_entropy(value)
        charset = set(value)
        if charset <= HEX_CHARSET and len(value) >= 32 and entropy > HEX_ENTROPY_THRESHOLD:
            findings.append("high_entropy_hex_assignment")
        elif (
            charset <= BASE64_CHARSET
            and len(value) >= 24
            and entropy > BASE64_ENTROPY_THRESHOLD
        ):
            findings.append("high_entropy_base64_assignment")
    return findings


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True)


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def tracked_files() -> list[Path]:
    return [ROOT / line for line in git("ls-files").splitlines() if line]


def history_commits() -> list[str]:
    return [line for line in git("rev-list", "HEAD").splitlines() if line]


def commit_changed_names(commit: str) -> list[str]:
    data = git_bytes("diff-tree", "-z", "--no-commit-id", "--name-status", "-r", "-M", commit)
    items = [item.decode("utf-8", errors="surrogateescape") for item in data.split(b"\0") if item]
    paths: list[str] = []
    index = 0
    while index < len(items):
        status = items[index]
        index += 1
        status_code = status[:1]
        if status_code in {"R", "C"}:
            index += 1
            if index < len(items):
                paths.append(items[index])
            index += 1
        elif status_code == "D":
            index += 1
        else:
            if index < len(items):
                paths.append(items[index])
            index += 1
    return paths


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
        data = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{commit}:{path}"],
            stderr=subprocess.DEVNULL,
        )
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
        for rule_name in _entropy_findings(line):
            findings.append(f"{label}:{line_number}: {rule_name}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_no_secret_patterns.py",
        description="Check tracked files for secret-shaped text.",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="Scan all commits reachable from local refs (needs full git fetch).",
    )
    args = parser.parse_args(argv)

    findings = scan_history() if args.history else scan_worktree()
    if findings:
        print(
            "Secret-shaped text found. Replace real or example-looking values with neutral placeholders.",
            file=sys.stderr,
        )
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK: no secret-shaped text found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
