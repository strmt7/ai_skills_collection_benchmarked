"""Control the pinned docs-from-code Python extractor on synthetic source."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

EXTRACTOR_SHA256 = "5f704c5c0399b661943ff663c3545d33c53540cda4ff7a509c0a1b7949ad8e90"
FIXTURE = """\
from flask import Flask
from fastapi import FastAPI
app = Flask(__name__)
api = FastAPI()

class Cache:
    def get(self, key):
        return lambda function: function

cache = Cache()

@app.route("/health", methods=["GET"])
def flask_health():
    return "ok"

@api.get("/items")
def fastapi_items():
    return []

@cache.get("/cached")
def cached_value():
    return 1

def combine(a: int = 1, /, *values: int, flag: bool = False, **options: str) -> str:
    return str(a)
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extractor", required=True, type=Path)
    args = parser.parse_args()
    source = args.extractor.read_bytes()
    if hashlib.sha256(source).hexdigest() != EXTRACTOR_SHA256:
        raise ValueError("Unexpected extractor bytes")
    with tempfile.TemporaryDirectory(prefix="docs-from-code-control-") as temp:
        root = Path(temp)
        project = root / "project"
        project.mkdir()
        (project / "app.py").write_text(FIXTURE, encoding="utf-8")
        extractor = root / "extract_py.py"
        extractor.write_bytes(source)
        output = root / "out.json"
        subprocess.run([sys.executable, str(extractor), str(project), str(output)], check=True, capture_output=True)
        result = json.loads(output.read_text(encoding="utf-8"))
    routes = sorted((route["method"], route["path"], route["handler"]) for route in result["routes"])
    signature = next(function["signature"] for function in result["functions"] if function["name"] == "combine")
    expected_routes = [("GET", "/cached", "cached_value"), ("GET", "/items", "fastapi_items")]
    if routes != expected_routes or signature != "def combine(a: int, flag: bool) -> str":
        raise ValueError(f"Unexpected extractor output: {routes!r} {signature!r}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "extractor_sha256": EXTRACTOR_SHA256,
                "fixture_sha256": hashlib.sha256(FIXTURE.encode("utf-8")).hexdigest(),
                "routes": routes,
                "flask_route_detected": any(route[2] == "flask_health" for route in routes),
                "unrelated_decorator_reported_as_route": any(route[2] == "cached_value" for route in routes),
                "extracted_signature": signature,
                "expected_source_signature": "def combine(a: int = 1, /, *values: int, flag: bool = False, **options: str) -> str",
                "graphify_executed": False,
                "agent_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
