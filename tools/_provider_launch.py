"""Automatically provision and recover checkout-owned development providers."""

from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import http.client
import json
import os
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any, BinaryIO

import _agent_tool_runtime as owned
import cocoindex_tool as provider
import crawl4ai_tool as crawler
from _catalog_publication import checked_path

ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, value: Any) -> None:
    temporary = checked_path(path.parent, path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")
    checked_path(path.parent, path.name)
    os.replace(temporary, path)


@contextlib.contextmanager
def exclusive(path: Path, timeout: float = 600) -> Iterator[BinaryIO]:
    import msvcrt

    with path.open("a+b") as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\0")
            stream.flush()
        started = time.monotonic()
        while True:
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                break
            except OSError as error:
                if error.errno not in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise
                if time.monotonic() - started >= timeout:
                    raise TimeoutError("Another provider setup still owns the checkout cache lock") from None
                time.sleep(0.1)
        try:
            yield stream
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def identity(root: Path, name: str = "cocoindex") -> str:
    tool = provider if name == "cocoindex" else crawler
    names = [
        "tools/" + name
        for name in [
            "_provider_launch.py",
            "_agent_tool_runtime.py",
            "_windows_owned_python.py",
            *(
                [
                    "cocoindex_tool.py",
                    "cocoindex_runtime.py",
                    "prepare_cocoindex_source.py",
                    "verify_cocoindex_wheel.py",
                    "search_semantic_corpus.py",
                ]
                if name == "cocoindex"
                else [
                    "crawl4ai_tool.py",
                    "crawl4ai_runtime.py",
                    "crawl4ai_capture.py",
                    "prepare_crawl4ai_source.py",
                    "verify_crawl4ai_wheel.py",
                ]
            ),
        ]
    ]
    value = {
        "provider_inputs": tool.identity(root),
        "implementation": owned.input_identity(root, names),
        "base_python": str(Path(sys.base_prefix).resolve(strict=True)),
        "python_version": list(sys.version_info[:3]),
    }
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def admit_owner(base: Path, root: Path, name: str = "cocoindex") -> None:
    owner = checked_path(base, "owner.json")
    expected = {"schema_version": 1, "purpose": "ai-skills-automatic-" + name, "source_root": str(root)}
    if owner.exists():
        observed = json.loads(owner.read_bytes())
        if observed != expected or type(observed["schema_version"]) is not int:
            raise ValueError("The automatic provider cache belongs to another purpose or checkout")
    else:
        if any(path.name != "setup.lock" for path in base.iterdir()):
            raise ValueError("Refusing to adopt an unowned provider cache")
        write_json(owner, expected)


def prepare(root: Path, name: str = "cocoindex") -> tuple[Path, dict[str, Any]]:
    tool = provider if name == "cocoindex" else crawler
    base = owned.home_path(root, root / (".venv/agent-tools/automatic-" + name))
    if (
        base.exists()
        and not checked_path(base, "owner.json").exists()
        and any(path.name != "setup.lock" for path in base.iterdir())
    ):
        raise ValueError("Refusing to adopt an unowned provider cache")
    base.mkdir(parents=True, exist_ok=True)
    with exclusive(checked_path(base, "setup.lock")):
        admit_owner(base, root, name)
        fingerprint = identity(root, name)
        active = checked_path(base, "active-" + fingerprint[:16] + ".json")
        diagnostics = checked_path(base, "logs/" + uuid.uuid4().hex[:12])
        diagnostics.mkdir(parents=True)
        rejected: str | None = None
        if active.exists():
            raw = active.read_bytes()
            try:
                receipt = json.loads(raw)
                if not isinstance(receipt, dict) or type(receipt.get("schema_version")) is not int:
                    raise ValueError("The active profile receipt has an invalid schema")
                if receipt["schema_version"] != 1:
                    raise ValueError("The active profile receipt has an unsupported schema")
                name = receipt["profile"]
                if receipt["identity"] != fingerprint or not isinstance(name, str):
                    raise ValueError("The active profile differs from its qualified implementation and base")
                if (
                    not name.startswith("profile-")
                    or len(name) != 20
                    or any(character not in "0123456789abcdef" for character in name[8:])
                ):
                    raise ValueError("The active provider profile name is not canonical")
                home = checked_path(base, name)
                result = tool.verify(home)
                return home, {**result, "automatic_setup": {"newly_installed": False, "identity": fingerprint}}
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                rejected = str(error)
                with (diagnostics / "rejected-pointer.native").open("xb") as stream:
                    stream.write(raw)
                write_json(
                    diagnostics / "rejected-profile.json",
                    {"pointer_sha256": hashlib.sha256(raw).hexdigest(), "failure": rejected[:4096]},
                )
        home = checked_path(base, "profile-" + uuid.uuid4().hex[:12])
        try:
            result = tool.setup(home)
        except Exception as error:
            write_json(
                diagnostics / "setup-failure.json",
                {"profile": str(home), "identity": fingerprint, "failure": str(error)[:4096]},
            )
            raise
        write_json(active, {"schema_version": 1, "identity": fingerprint, "profile": home.name})
        return home, {
            **result,
            "automatic_setup": {
                "newly_installed": True,
                "recovered_previous_profile": rejected is not None,
                "identity": fingerprint,
                "diagnostics": str(diagnostics),
            },
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=["cocoindex", "crawl4ai"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    selected = build_parser().parse_args(argv)
    tool = provider if selected.provider == "cocoindex" else crawler
    arguments = tool.build_parser().parse_args(selected.arguments)
    try:
        owned.require_interpreter((3, 13, 18))
        if arguments.home is not None:
            raise ValueError(
                "The automatic launcher manages its own profiles; select an explicit home with the low-level tool"
            )
        home, result = prepare(ROOT, selected.provider)
        result = tool.execute(arguments, home, result)
        if diagnostics := os.environ.get("AI_SKILLS_BOOTSTRAP_DIAGNOSTICS"):
            result["bootstrap_diagnostics"] = diagnostics
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, http.client.HTTPException) as error:
        result = {"ok": False, "errors": [str(error)[:4096]]}
    print(json.dumps(result, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())
