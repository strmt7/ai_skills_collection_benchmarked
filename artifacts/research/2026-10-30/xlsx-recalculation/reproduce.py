"""Control spreadsheet recalculation outcomes with source-bound simulated processes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

import openpyxl

HASHES = {
    "mirror": "e8251c94ae0c6678b6793d56d2620dd2daf7c73e1da00db6c4aaf4d5e34acd8e",
    "pinned": "cf419d15e02965aeaec17773c05b61303f7f520f67fa2696547e7da07502eac7",
    "current": "66f6e726d5a53cfabea0b6471d6669deb95e54e96cb7913b687e4388da1bb3d9",
}


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected source bytes: {path.name}")
    return data


def cached_value(path: Path) -> object:
    book = openpyxl.load_workbook(path, data_only=True)
    try:
        return book.active["A1"].value
    finally:
        book.close()


def exercise(source: bytes, *, current: bool, root: Path) -> dict[str, object]:
    script = root / ("current.py" if current else "original.py")
    script.write_bytes(source)
    fake_office = types.ModuleType("office")
    fake_soffice = types.ModuleType("office.soffice")
    fake_soffice.get_soffice_env = lambda: {}
    fake_soffice.run_soffice = lambda *args, **kwargs: None
    results = {}
    with patch.dict(sys.modules, {"office": fake_office, "office.soffice": fake_soffice}):
        spec = importlib.util.spec_from_file_location("xlsx_recalc_control", script)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot import the pinned helper")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name, value, exit_code in (
            ("neutral_text", "ordinary text", 0),
            ("literal_error_text", "note: #N/A appears in source", 0),
            ("actual_error_cell", "#DIV/0!", 0),
            ("timed_out_formula", "=1+1", 124),
            ("process_failure", "ordinary text", 1),
        ):
            path = root / f"{name}.xlsx"
            book = openpyxl.Workbook()
            book.active["A1"] = value
            data_type = book.active["A1"].data_type
            book.save(path)
            book.close()
            before = cached_value(path)

            def fake_run(command, *, _path=path, _exit_code=exit_code, **kwargs):
                if _exit_code == 0:
                    stat = _path.stat()
                    os.utime(_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
                return subprocess.CompletedProcess(
                    command, _exit_code, "", "controlled failure" if _exit_code == 1 else ""
                )

            setup = ("file:///controlled-profile", None) if current else True
            with (
                patch.object(module, "setup_libreoffice_macro", return_value=setup),
                patch.object(module.platform, "system", return_value="Linux"),
                patch.object(module.subprocess, "run", side_effect=fake_run),
            ):
                outcome = module.recalc(str(path))
            results[name] = {
                "cell_type": data_type,
                "cached_before": before,
                "cached_after": cached_value(path),
                "status": outcome.get("status"),
                "error_returned": "error" in outcome,
                "total_errors": outcome.get("total_errors"),
            }
    wrapper = """import runpy, sys, types
office = types.ModuleType('office')
soffice = types.ModuleType('office.soffice')
soffice.get_soffice_env = lambda: {}
soffice.run_soffice = lambda *args, **kwargs: None
sys.modules['office'] = office
sys.modules['office.soffice'] = soffice
sys.argv = [sys.argv[1], sys.argv[2]]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    process = subprocess.run(
        [sys.executable, "-I", "-c", wrapper, str(script), str(root / "not-present.xlsx")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    payload = json.loads(process.stdout)
    results["missing_file_cli"] = {"exit_code": process.returncode, "json_error": "error" in payload}
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    for name in HASHES:
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    sources = {name: pinned(getattr(args, name), digest) for name, digest in HASHES.items()}
    equivalent = ast.dump(ast.parse(sources["mirror"])) == ast.dump(ast.parse(sources["pinned"]))
    if not equivalent:
        raise ValueError("Mirror and pinned source ASTs differ")
    with tempfile.TemporaryDirectory(prefix="xlsx-recalc-control-") as temporary:
        root = Path(temporary)
        outcomes = {name: exercise(source, current=name == "current", root=root) for name, source in sources.items()}
    if outcomes["mirror"] != outcomes["pinned"]:
        raise ValueError("Pinned and mirrored outcomes differ")
    original, current = outcomes["mirror"], outcomes["current"]
    for result in (original, current):
        if result["neutral_text"]["status"] != "success" or result["actual_error_cell"]["status"] != "errors_found":
            raise ValueError("Expected neutral or actual-error control did not behave as expected")
        if result["literal_error_text"]["cell_type"] != "s" or result["literal_error_text"]["status"] != "errors_found":
            raise ValueError("Expected literal-text behavior changed")
        if not result["process_failure"]["error_returned"]:
            raise ValueError("Expected process-failure control did not return an error")
    if original["missing_file_cli"] != {"exit_code": 0, "json_error": True}:
        raise ValueError("Expected original CLI error behavior changed")
    if current["missing_file_cli"] != {"exit_code": 1, "json_error": True}:
        raise ValueError("Expected current CLI error behavior changed")
    timeout_old, timeout_new = original["timed_out_formula"], current["timed_out_formula"]
    if timeout_old["cached_before"] is not None or timeout_old["cached_after"] is not None:
        raise ValueError("Formula unexpectedly has a cached value")
    if timeout_old["status"] != "success" or not timeout_new["error_returned"]:
        raise ValueError("Expected timeout distinction changed")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "openpyxl": openpyxl.__version__,
                "source_sha256": HASHES,
                "mirror_and_pinned_ast_match": equivalent,
                "process_and_profile_simulated": True,
                "libreoffice_executed": False,
                "agent_scored": False,
                "outcomes": outcomes,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
