"""Admit the complete isolated crawler graph and native browser payloads."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any, cast

import _bootstrap_doctor as doctor
import verify_crawl4ai_wheel as wheel
from _catalog_publication import checked_path
from prepare_crawl4ai_source import ROOT, digest, files


def check_runtime(home: Path) -> dict[str, Any]:
    if Path(sys.prefix).resolve() != checked_path(home, "runtime").resolve():
        raise ValueError("Run this worker only in its owned crawler runtime")
    pin = json.loads((ROOT / "toolchains/crawl4ai/source.json").read_bytes())
    count = wheel.installed_files(pin)
    observation = doctor.observation(
        Path(sys.prefix) / "Lib/site-packages", [home / "admission/requirements.txt"], ["crawl4ai"]
    )
    if observation["python"] != "3.13.18" or observation["bits"] != 64 or observation["isolated"] != 1:
        raise ValueError("Crawler runtime differs from its qualified Windows x64 interpreter")
    return {
        "source_files_admitted": count,
        "runtime_distributions": len(cast(list[tuple[str, str]], observation["packages"])),
    }


def check_browser(home: Path) -> dict[str, Any]:
    pin = json.loads((ROOT / "toolchains/crawl4ai/browser.json").read_bytes())
    if importlib.metadata.version(pin["driver"]) != pin["driver_version"]:
        raise ValueError("Browser driver differs from the qualified payload pin")
    browser = checked_path(home, "browsers")
    expected = {record["path"]: record for record in pin["files"]}
    observed = {}
    for directory, markers in pin["directories"].items():
        payload = checked_path(browser, directory)
        for name, sha256 in files(payload).items():
            if name in markers:
                if checked_path(payload, name).stat().st_size:
                    raise ValueError("Native installer marker must be empty")
                continue
            observed[directory + "/" + name] = sha256
    if set(observed) != set(expected):
        raise ValueError("Installed browser payload inventory differs from the qualified pin")
    for name, sha256 in observed.items():
        if sha256 != expected[name]["sha256"] or checked_path(browser, name).stat().st_size != expected[name]["bytes"]:
            raise ValueError("Installed browser payload differs: " + name)
    return {
        "browser_files_admitted": len(observed),
        "browser_version": pin["chromium_version"],
        "browser_pin_sha256": digest((ROOT / "toolchains/crawl4ai/browser.json").read_bytes()),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("command", choices=["check-runtime", "check-browser"])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    operation = check_runtime if args.command == "check-runtime" else check_browser
    print(json.dumps(operation(args.home), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
