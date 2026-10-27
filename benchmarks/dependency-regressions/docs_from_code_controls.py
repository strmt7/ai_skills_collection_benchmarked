#!/usr/bin/env python3
"""Reproduce source-bound Python documentation extractor defects in isolation."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = Path(
    "included/skills/by-category/documents-spreadsheets-presentations/"
    "reddit-verified-gtm-registry/docs-from-code/scripts/extract_py.py"
)
FIXTURE_NAME = "docs_from_code_fixture.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature_matches(signature: str) -> bool:
    expected = (
        'def sample(name: str = "x", /, count: int = 1, *args: str, flag: bool = False, **kwargs: int) -> str: pass'
    )
    try:
        actual = ast.parse(f"{signature}:\n    pass\n").body[0]
        reference = ast.parse(expected).body[0]
    except (IndexError, SyntaxError, ValueError):
        return False
    return (
        isinstance(actual, ast.FunctionDef)
        and isinstance(reference, ast.FunctionDef)
        and actual.returns is not None
        and reference.returns is not None
        and actual.name == reference.name
        and ast.dump(actual.args) == ast.dump(reference.args)
        and ast.dump(actual.returns) == ast.dump(reference.returns)
    )


def assess(result: dict[str, Any]) -> dict[str, bool]:
    """Check observed values against independently specified desired behavior."""
    cases = result["cases"]
    return {
        "flask_routes": Counter((route["method"], route["path"]) for route in cases["flask"]["routes"])
        == Counter({("GET", "/users"): 1, ("POST", "/users"): 1}),
        "false_decorator": cases["false_decorator"]["routes"] == [],
        "fastapi_mount": Counter((route["method"], route["path"]) for route in cases["fastapi_mount"]["routes"])
        == Counter({("GET", "/api/v1/users"): 1}),
        "invalid_source": cases["invalid_source"]["exit_code"] != 0 and not cases["invalid_source"]["output_exists"],
        "signature": signature_matches(cases["signature"]["signature"]),
    }


def run_controls(root: Path, fixture: Path) -> dict[str, Any]:
    """Run the immutable original and fail if observed baseline behavior changes."""
    sys.path.insert(0, str(root / "tools"))
    from isolated_python import run_isolated

    original = root / ORIGINAL
    before = {"original": digest(original), "fixture": digest(fixture)}
    with tempfile.TemporaryDirectory(prefix="docs-from-code-control-") as directory:
        stage = Path(directory)
        shutil.copyfile(original, stage / "original.py")
        shutil.copyfile(fixture, stage / "candidate.py")
        invocation = run_isolated(stage, ["original.py", "candidate.py"], {}, timeout=45)
    if before != {"original": digest(original), "fixture": digest(fixture)}:
        raise ValueError("control inputs changed during execution")
    result = invocation.get("candidate_response", {}).get("result", {})
    if (
        invocation["status"] != "completed"
        or not invocation["cleanup_verified"]
        or result.get("platform") != "linux"
        or result.get("uid") != 65534
        or result.get("temporary_directory_removed") is not True
        or result.get("provider_calls") != 0
    ):
        raise ValueError("isolated control did not complete and clean up as required")
    desired_behavior = assess(result)
    return {
        "schema_version": 1,
        "evidence_class": "original-python-documentation-extractor-contract-controls",
        "reproduced_all_five_defects": not any(desired_behavior.values()),
        "desired_behavior_passed": desired_behavior,
        "source_sha256": before["original"],
        "fixture_sha256": before["fixture"],
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "scope": "Original source and synthetic local fixtures; no AI, provider or deployed framework benchmark.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New receipt; never overwritten")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    result = run_controls(ROOT, Path(__file__).with_name(FIXTURE_NAME))
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(
        json.dumps(
            {"reproduced_all_five_defects": result["reproduced_all_five_defects"], "agent_efficacy_scored": False}
        )
    )
    return int(not result["reproduced_all_five_defects"])


if __name__ == "__main__":
    raise SystemExit(main())
