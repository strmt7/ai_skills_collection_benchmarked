"""Reproduce selected design-search and renderer observations in temporary copies."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / "included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design"
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAEklEQVR4nGOUs4liYGBgYgADAAheALijMW7VAAAAAElFTkSuQmCC"
)


def capture(script: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    return subprocess.run(
        [sys.executable, "-B", str(script), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )


def run_control(source: Path, manifest_path: Path = HERE / "source-manifest.json") -> dict[str, Any]:
    """Verify the selected source bytes, then exercise only copied local inputs."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = manifest["files"]
    payloads = {}
    for name, expected in files.items():
        data = (source / name).read_bytes()
        if hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest() != expected:
            raise ValueError(f"Source differs from the recorded manifest: {name}")
        payloads[name] = data

    with tempfile.TemporaryDirectory(prefix="design-search-control-") as temporary:
        base = Path(temporary)
        for fixture in ("complete", "missing"):
            for name, data in payloads.items():
                path = base / fixture / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        for name in ("data/logo/styles.csv", "data/cip/deliverables.csv"):
            (base / "missing" / name).unlink()

        searches = []
        for kind, query, domain in (("logo", "minimalist clean", "style"), ("cip", "business card", "deliverable")):
            for fixture in ("complete", "missing"):
                root = base / fixture
                result = capture(root / "scripts" / kind / "search.py", [query, "--domain", domain, "--json"], root)
                body = json.loads(result.stdout)
                searches.append(
                    {"kind": kind, "fixture": fixture, "exit_code": result.returncode, "error_present": "error" in body}
                )

        brief = []
        for fixture in ("complete", "missing"):
            root = base / fixture
            result = capture(
                root / "scripts/cip/search.py", ["healthcare", "--cip-brief", "--brand", "Sample", "--json"], root
            )
            body = json.loads(result.stdout)
            brief.append(
                {
                    "fixture": fixture,
                    "exit_code": result.returncode,
                    "error_present": "error" in body,
                    "deliverables": [item["Deliverable"] for item in body["recommended_deliverables"]],
                }
            )

        lexical = []
        root = base / "complete"
        for query in ("uniform", "uniforms", "badge", "badges"):
            result = capture(root / "scripts/cip/search.py", [query, "--domain", "deliverable", "--json"], root)
            body = json.loads(result.stdout)
            lexical.append({"query": query, "exit_code": result.returncode, "count": body["count"]})

        images = base / "images"
        (images / "empty").mkdir(parents=True)
        (images / "valid").mkdir()
        (images / "valid" / "business-card.png").write_bytes(PNG)
        renderer = []
        for fixture in ("missing", "empty", "valid"):
            output = base / f"{fixture}.html"
            result = capture(
                root / "scripts/cip/render-html.py",
                [
                    "--brand",
                    "Sample",
                    "--industry",
                    "healthcare",
                    "--images",
                    str(images / fixture),
                    "--output",
                    str(output),
                ],
                root,
            )
            renderer.append(
                {
                    "fixture": fixture,
                    "exit_code": result.returncode,
                    "reported_error": "Error:" in result.stdout,
                    "output_exists": output.is_file(),
                }
            )
    return {
        "skill_id": manifest["skill_id"],
        "source_commit": manifest["source_commit"],
        "searches": searches,
        "brief": brief,
        "lexical": lexical,
        "renderer": renderer,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = (json.dumps(run_control(args.source), indent=2, sort_keys=True) + "\n").encode("utf-8")
        if args.check:
            if args.output.read_bytes() != data:
                raise ValueError("Recorded observations differ from the current control")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(data)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "agent_efficacy_scored": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
