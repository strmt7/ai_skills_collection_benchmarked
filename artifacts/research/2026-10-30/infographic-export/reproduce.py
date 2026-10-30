"""Exercise source-bound infographic exports with absent SVG converters."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import locale
import os
import platform
import shutil
import sys
import tempfile
from pathlib import Path

SOURCE = "included/skills/by-category/documents-spreadsheets-presentations/creative-reference/create-infographics/scripts/export.py"
SOURCE_SHA256 = "e250a6992812a3721c763ff87a36783752b605a33d7e45a601c0271f88146005"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32":
        raise ValueError("This component control requires Windows")
    root = args.root.resolve()
    source = root / SOURCE
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Unexpected exporter source bytes")
    sys.path.insert(0, str(root / "tools"))
    from _windows_trial_process import run_owned

    scratch = args.scratch.resolve()
    if not scratch.is_dir():
        raise ValueError("Scratch directory must exist")
    results = {}
    with tempfile.TemporaryDirectory(prefix="infographic-control-", dir=scratch) as temporary:
        workspace = Path(temporary)
        (workspace / "temp").mkdir()
        page = workspace / "input.html"
        page.write_text(
            "<!doctype html><html><body><h1>Local fixture</h1><p>42 units</p></body></html>", encoding="utf-8"
        )
        os.environ["TEMP"] = os.environ["TMP"] = str(workspace / "temp")
        os.environ["PATH"] = str(Path(os.environ["SYSTEMROOT"]) / "System32")
        if any(shutil.which(name) for name in ("inkscape", "pdf2svg")):
            raise ValueError("The controlled executable path has an SVG converter")
        for name, export_format, flags in (
            ("all_default", "all", []),
            ("all_utf8", "all", ["-X", "utf8"]),
            ("svg_utf8", "svg", ["-X", "utf8"]),
        ):
            directory = workspace / name
            directory.mkdir()
            output = directory / "result"
            with (
                tempfile.TemporaryFile() as stdin,
                tempfile.TemporaryFile() as stdout,
                tempfile.TemporaryFile() as stderr,
            ):
                report = run_owned(
                    [
                        sys.executable,
                        "-I",
                        *flags,
                        str(source),
                        "--input",
                        str(page),
                        "--output",
                        str(output),
                        "--format",
                        export_format,
                        "--no-serve",
                    ],
                    cwd=workspace,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=70,
                    output_limit=100000,
                )
                stdout.seek(0)
                stderr.seek(0)
                encoding = "utf-8" if flags else locale.getpreferredencoding(False)
                text = stdout.read().decode(encoding, errors="replace")
                error = stderr.read().decode(encoding, errors="replace")
            for original, replacement in (
                (str(workspace), "<workspace>"),
                (str(root), "<repository>"),
                (sys.base_prefix, "<python>"),
            ):
                text = text.replace(original, replacement)
                error = error.replace(original, replacement)
            files = {}
            for ext in ("png", "pdf", "svg"):
                path = output.with_suffix("." + ext)
                files[ext] = {
                    "exists": path.is_file(),
                    "signature": path.read_bytes()[:8].hex() if path.is_file() else None,
                }
            if report["termination_reason"] is not None or report["job_active_processes_after_cleanup"] != 0:
                raise ValueError(f"Unresolved execution problem: {name}")
            results[name] = {
                "process": report,
                "output_encoding": encoding,
                "stdout": text,
                "stderr": error,
                "files": files,
            }
    for name in ("all_utf8", "svg_utf8"):
        item = results[name]
        if (
            item["process"]["exit_code"] != 0
            or item["files"]["svg"]["exists"]
            or "SVG export skipped" not in item["stdout"]
        ):
            raise ValueError(f"Expected no-converter behavior changed: {name}")
    if "All formats exported:" not in results["all_utf8"]["stdout"]:
        raise ValueError("Expected all-formats report changed")
    if results["all_utf8"]["files"]["png"]["signature"] != "89504e470d0a1a0a" or not results["all_utf8"]["files"][
        "pdf"
    ]["signature"].startswith("25504446"):
        raise ValueError("Expected PNG/PDF output signatures missing")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "playwright": importlib.metadata.version("playwright"),
                "source_sha256": SOURCE_SHA256,
                "converter_path_excludes_tools": True,
                "server_started": False,
                "html_has_external_resources": False,
                "agent_scored": False,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
