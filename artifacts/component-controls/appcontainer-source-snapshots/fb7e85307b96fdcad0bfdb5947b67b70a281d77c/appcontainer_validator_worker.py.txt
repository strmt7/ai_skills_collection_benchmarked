"""Untrusted-side API adapter; it receives inputs but no expected verdicts."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def invoke(request: dict[str, Any]) -> dict[str, Any]:
    specification = importlib.util.spec_from_file_location("submitted_validator", request["module"])
    if specification is None or specification.loader is None:
        raise ValueError("Cannot load submitted validator")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    if request.get("schema_override"):
        module.__dict__["SCHEMA_PATH"] = Path(request["schema_override"])
    return {"kind": "candidate_result", "value": module.validate_artifact(Path(request["artifact"]))}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        request = json.loads(args.request.read_bytes())
        result = invoke(request)
        encoded = json.dumps(result, allow_nan=False)
    except (Exception, SystemExit, KeyboardInterrupt) as error:
        encoded = json.dumps({"kind": "candidate_error", "exception_type": type(error).__name__})
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
