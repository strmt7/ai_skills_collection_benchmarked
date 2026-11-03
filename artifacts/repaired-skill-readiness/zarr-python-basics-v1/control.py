"""Run selected Zarr API controls against the locked example and repaired entrypoint."""

from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import json
import platform
import re
import tempfile
from pathlib import Path

import numpy as np
import zarr
from zarr.codecs import BloscCodec
from zarr.storage import MemoryStore

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/zarr-python-basics"
)
MIRROR = (
    ROOT / "included/skills/by-category/science-research-data-analysis/latest-release-community/zarr-python/SKILL.md"
)
ORIGINAL_SHA256 = "e5dfd7907be47cf782af6e62988829968b36a70521881253c2f4ff7574858088"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def block(markdown: str, heading: str) -> str:
    pattern = rf"(?m)^###? {re.escape(heading)}\s*\n\s*```python\n(.*?)\n```"
    matches = re.findall(pattern, markdown, flags=re.DOTALL)
    if len(matches) != 1:
        raise ValueError(f"Expected one Python block for {heading}, found {len(matches)}")
    return matches[0]


def expect_exception(
    label: str, code: str, namespace: dict[str, object], expected: type[Exception], message: str
) -> dict[str, str]:
    try:
        exec(compile(code, label, "exec"), namespace)
    except expected as exc:
        if message not in str(exc):
            raise RuntimeError(f"{label} failed for an unexpected reason") from exc
        return {"case": label, "exception": type(exc).__name__, "outcome": "expected_failure"}
    raise RuntimeError(f"{label} unexpectedly succeeded; re-evaluate the documented contract")


def main() -> None:
    original_bytes = (OVERLAY / "provenance/original.SKILL.md").read_bytes()
    if digest(original_bytes) != ORIGINAL_SHA256:
        raise ValueError("Locked original source does not match the admitted digest")
    if importlib.metadata.version("zarr") != "3.4.2" or np.__version__ != "2.5.4":
        raise ValueError("Control requires the recorded Zarr and NumPy versions")
    if MIRROR.read_bytes().replace(b"\r\n", b"\n") != original_bytes:
        raise ValueError("Mirror differs from the preserved original source")
    original = original_bytes.decode("utf-8")
    overlay_bytes = (OVERLAY / "SKILL.md").read_bytes()
    overlay = overlay_bytes.decode("utf-8")
    namespace: dict[str, object] = {"zarr": zarr, "np": np, "BloscCodec": BloscCodec}
    namespace["z"] = zarr.create_array(store=MemoryStore(), shape=(2, 2), chunks=(2, 2), dtype="int32")

    resize = ast.parse(block(original, "Resizing and Appending")).body[0]
    if not isinstance(resize, ast.Expr) or ast.unparse(resize) != "z.resize(15000, 15000)":
        raise ValueError("Unexpected upstream resize example")
    outcomes = [expect_exception("upstream_resize", ast.unparse(resize), namespace, TypeError, "positional argument")]

    compression = ast.parse(block(original, "Configuring Compression"))
    candidates = [
        n
        for n in compression.body
        if isinstance(n, ast.Assign)
        and isinstance(n.value, ast.Call)
        and any(k.arg == "codecs" for k in n.value.keywords)
    ]
    if len(candidates) != 3:
        raise ValueError("Unexpected upstream compression examples")
    first = candidates[0]
    # The source expression uses a literal directory. Redirect only the store to
    # an isolated temporary location while keeping the original API arguments.
    store = next(k for k in first.value.keywords if k.arg == "store")
    with tempfile.TemporaryDirectory() as temporary:
        store.value = ast.Constant(str(Path(temporary) / "data.zarr"))
        outcomes.append(
            expect_exception(
                "upstream_codecs", ast.unparse(first), namespace, TypeError, "unexpected keyword argument 'codecs'"
            )
        )

    profile = block(original, "Profiling and Debugging")
    if "z.nbytes_stored / 1e6" not in profile:
        raise ValueError("Unexpected upstream stored-byte example")
    outcomes.append(
        expect_exception(
            "upstream_nbytes_stored", "z.nbytes_stored / 1e6", namespace, TypeError, "unsupported operand type"
        )
    )
    for heading, name in (
        ("Thread-Safe Operations", "ThreadSynchronizer"),
        ("Process-Safe Operations", "ProcessSynchronizer"),
    ):
        node = ast.parse(block(original, heading)).body[0]
        if ast.unparse(node) != f"from zarr import {name}":
            raise ValueError(f"Unexpected upstream {name} example")
        outcomes.append(
            expect_exception(
                "upstream_" + name, ast.unparse(node), namespace, ImportError, f"cannot import name '{name}'"
            )
        )

    local: dict[str, object] = {}
    exec(compile(block(overlay, "Create, resize, and inspect"), "overlay", "exec"), local)
    values = local["values"]
    if not isinstance(values, np.ndarray) or values.shape != (3, 2):
        raise RuntimeError("Overlay produced the wrong shape")
    if not np.array_equal(values, np.array([[1, 2], [3, 4], [0, 0]], dtype="int32")):
        raise RuntimeError("Overlay lost values or produced incorrect fill values")
    stored = local["stored_bytes"]
    if not isinstance(stored, int) or stored <= 0:
        raise RuntimeError("Overlay did not return a positive integer stored size")
    outcomes.append({"case": "overlay_example", "outcome": "pass"})
    result = {
        "agent_performance_tested": False,
        "control_sha256": digest(Path(__file__).read_bytes()),
        "numpy_version": np.__version__,
        "original_sha256": digest(original_bytes),
        "outcomes": outcomes,
        "overlay_sha256": digest(overlay_bytes),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "scope": "Selected in-memory array API examples only; no agent or concurrency trial",
        "zarr_version": importlib.metadata.version("zarr"),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
