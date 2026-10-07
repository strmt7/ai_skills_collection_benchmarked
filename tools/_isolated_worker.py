"""Public candidate invocation protocol; contains no expected answers or scores."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def invoke(root: Path, entrypoint: str, request: Any) -> Any:
    """Import a staged Python entrypoint and call its run(request) function."""
    path = root / entrypoint
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location("candidate", path)
    if spec is None or spec.loader is None:
        raise ValueError("entrypoint cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules["candidate"] = module
    spec.loader.exec_module(module)
    return module.run(request)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("/submission"))
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--request-limit", type=int, required=True)
    parser.add_argument("--output-limit", type=int, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(args.request_limit + 1)
        if len(raw) > args.request_limit:
            raise ValueError("request exceeds protocol bound")
        request = json.loads(raw.decode("utf-8"))
        result = invoke(args.root, args.entrypoint, request)
        envelope = {"worker_status": "returned", "result": result}
    except Exception as exc:
        envelope = {"worker_status": "error", "error_type": type(exc).__name__, "detail": str(exc)[:2048]}
    try:
        output = json.dumps(envelope, allow_nan=False).encode("utf-8")
        if len(output) > args.output_limit:
            raise ValueError("result exceeds protocol bound")
    except (TypeError, ValueError):
        output = b'{"worker_status":"error","error_type":"InvalidResult"}'
    sys.stdout.buffer.write(output + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
