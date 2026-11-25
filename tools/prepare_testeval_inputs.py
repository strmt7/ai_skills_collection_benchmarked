"""Materialize only the inputs for the frozen public TestEval pilot."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import urlsplit
from urllib.request import urlopen

from collect_testeval_submission import ASSET_LIMIT, ROOT, load_profile, object_from, read_asset, sha256

PUBLISHER_REPO = "LLM4SoftwareTesting/TestEval"
ORIGINS = {"raw.githubusercontent.com", "files.pythonhosted.org"}


def download(url: str, digest: str) -> bytes:
    endpoint = urlsplit(url)
    if endpoint.scheme != "https" or endpoint.netloc not in ORIGINS:
        raise ValueError("Expected an official TestEval publisher or Python package endpoint")
    deadline = time.monotonic() + 30
    content = bytearray()
    with urlopen(url, timeout=15) as response:
        if response.status != 200 or response.url != url:
            raise ValueError("Unexpected response for the declared TestEval input")
        while block := response.read1(65536):
            content.extend(block)
            if len(content) > ASSET_LIMIT or time.monotonic() > deadline:
                raise ValueError("TestEval input exceeded its download budget")
    raw = bytes(content)
    if sha256(raw) != digest:
        raise ValueError("Downloaded TestEval input differs from its frozen identity")
    return raw


def projection(dataset: bytes, selection: dict[str, Any]) -> bytes:
    """Retain just the selected public task IDs and required publisher fields."""
    if sha256(dataset) != selection["publisher"]["dataset_sha256"]:
        raise ValueError("Dataset differs from the frozen TestEval publisher snapshot")
    selected = {row["task_num"] for row in selection["selected"]}
    rows = []
    for line in dataset.splitlines():
        row = object_from(line)
        if row["task_num"] in selected:
            rows.append(
                {
                    "task_num": row["task_num"],
                    "difficulty": row["difficulty"],
                    "func_name": row["func_name"],
                    "code": row["python_solution"],
                }
            )
    if len(rows) != len(selected) or {row["task_num"] for row in rows} != selected:
        raise ValueError("Publisher dataset differs from the frozen public selection")
    return "".join(json.dumps(row) + "\n" for row in rows).encode()


def prepare(output: Path) -> dict[str, Any]:
    raw, profile, selection = load_profile()
    publisher = selection["publisher"]
    if (
        selection["partition"] != "public_development"
        or publisher["repository"] != "https://github.com/" + PUBLISHER_REPO
    ):
        raise ValueError("Expected the frozen public TestEval development publisher")
    base = "https://raw.githubusercontent.com/" + PUBLISHER_REPO + "/" + publisher["commit"] + "/"
    output = output.resolve()
    if not output.is_relative_to(ROOT / ".venv"):
        raise ValueError("Use an asset cache in this checkout's ignored state")
    output.mkdir(parents=True, exist_ok=True)
    sources = {
        name: (base + name, digest) for name, digest in profile["publisher_inputs"].items() if name != "selected.jsonl"
    }
    sources.update(
        {
            row["path"]: (profile["wheel_sources"][row["project"]], row["sha256"])
            for row in profile["python_environment"]["wheels"]
        }
    )
    sources["selected.jsonl"] = (base + "data/leetcode-py.jsonl", profile["publisher_inputs"]["selected.jsonl"])
    acquired = []
    for name, (url, digest) in sources.items():
        target = output / name
        if not target.resolve().is_relative_to(output):
            raise ValueError("TestEval asset cache cannot write outside its declared directory")
        try:
            read_asset(target, digest)
        except FileNotFoundError:
            pass
        else:
            continue
        if name == "selected.jsonl":
            data = projection(download(url, publisher["dataset_sha256"]), selection)
            if sha256(data) != digest:
                raise ValueError("Derived projection differs from its frozen identity")
        else:
            data = download(url, digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(dir=target.parent) as scratch:
            temporary = Path(scratch) / "input.native"
            temporary.write_bytes(data)
            temporary.replace(target)
        acquired.append(name)
    return {"profile_sha256": sha256(raw), "asset_count": len(sources), "acquired": acquired}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(args.output)
    except (KeyError, OSError, ValueError) as error:
        print(f"TestEval input preparation failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
