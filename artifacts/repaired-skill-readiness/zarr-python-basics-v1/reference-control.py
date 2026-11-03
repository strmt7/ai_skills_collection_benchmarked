"""Check selected claims in the source-locked Zarr API reference."""

from __future__ import annotations

import ast
import hashlib
import json
import platform
import re
from pathlib import Path

import zarr
from zarr.storage import MemoryStore

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/zarr-python-basics"
)
REFERENCE = (
    ROOT
    / "included/skills/by-category/science-research-data-analysis/latest-release-community/zarr-python/references/api_reference.md"
)
REFERENCE_SHA256 = "68d983ea5bacfd410ca3f2d1e0c4d464e555724d882467bff5313fd48dbd40b9"


def main() -> None:
    source = REFERENCE.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(source).hexdigest() != REFERENCE_SHA256:
        raise ValueError("Reference changed; reassess the source-bound control")
    if (OVERLAY / "provenance/original.api_reference.md").read_bytes() != source:
        raise ValueError("Preserved reference differs from its mirror")
    if zarr.__version__ != "3.4.2":
        raise ValueError("Control requires Zarr 3.4.2")
    text = source.decode("utf-8")
    if "`chunks`: Tuple defining chunk dimensions" not in text or "`None` for no chunking" not in text:
        raise ValueError("Reference chunking claim changed")
    match = re.search(r"(?ms)^### Methods\s*\n\s*```python\n(.*?)\n```", text)
    if not match:
        raise ValueError("Reference methods block missing")
    calls = {}
    for node in ast.walk(ast.parse(match.group(1))):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "z"
            and node.func.attr in {"copy", "info_items"}
        ):
            if node.func.attr in calls:
                raise ValueError("Unexpected duplicate method example")
            calls[node.func.attr] = ast.unparse(node)
    if set(calls) != {"copy", "info_items"}:
        raise ValueError("Reference method examples changed")

    # This creates metadata in memory; it does not allocate a full data array.
    array = zarr.zeros(shape=(10000, 10000), chunks=None, store=MemoryStore(), dtype="f4")
    if array.chunks == array.shape:
        raise RuntimeError("Chosen example did not produce multiple chunks")
    failures = {}
    for name, expression in calls.items():
        try:
            eval(compile(expression, "reference", "eval"), {"z": array})
        except AttributeError as exc:
            if name not in str(exc):
                raise
            failures[name] = type(exc).__name__
        else:
            raise RuntimeError(name + " unexpectedly succeeded")
    print(
        json.dumps(
            {
                "agent_performance_tested": False,
                "control_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "reference_sha256": REFERENCE_SHA256,
                "zarr_version": zarr.__version__,
                "platform": platform.system(),
                "python_version": platform.python_version(),
                "shape": array.shape,
                "chunks": array.chunks,
                "method_failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
