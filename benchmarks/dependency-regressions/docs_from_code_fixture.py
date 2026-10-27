"""Execute the unchanged extractor against owned examples without scoring them."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

CASES = {
    "flask": {
        "app.py": """from flask import Flask
app = Flask(__name__)
@app.route("/users", methods=["GET", "POST"])
def users(): return "ok"
"""
    },
    "false_decorator": {
        "main.py": """class Cache:
    def get(self, name): return lambda fn: fn
cache = Cache()
@cache.get("/not-http")
def sample(): return 1
"""
    },
    "fastapi_mount": {
        "app.py": """from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix="/v1")
@router.get("/users")
def users(): return []
app.include_router(router, prefix="/api")
"""
    },
    "invalid_source": {"main.py": "def broken(\n"},
    "signature": {
        "main.py": """def sample(name: str = "x", /, count: int = 1, *args: str, flag: bool = False, **kwargs: int) -> str:
    return name
"""
    },
}


def run(_request: object) -> dict[str, Any]:
    results = {}
    with tempfile.TemporaryDirectory(prefix="extractor-fixtures-") as temp:
        root = Path(temp)
        for name, files in CASES.items():
            project = root / name
            project.mkdir()
            for filename, text in files.items():
                (project / filename).write_text(text, encoding="utf-8")
            output = root / f"{name}.json"
            invocation = subprocess.run(
                [sys.executable, "-I", str(Path(__file__).with_name("original.py")), str(project), str(output)],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            metadata = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
            results[name] = {
                "exit_code": invocation.returncode,
                "output_exists": output.exists(),
                "routes": [{"method": route["method"], "path": route["path"]} for route in metadata["routes"]]
                if metadata
                else [],
                "signature": next((item["signature"] for item in metadata["functions"] if item["name"] == "sample"), "")
                if metadata
                else "",
            }
    return {
        "cases": results,
        "uid": getattr(os, "getuid", lambda: None)(),
        "platform": sys.platform,
        "temporary_directory_removed": not root.exists(),
        "provider_calls": 0,
    }
