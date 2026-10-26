"""Run admitted local-only CocoIndex operations inside their owned interpreter."""

from __future__ import annotations

import argparse
import contextlib
import importlib.metadata
import io
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import prepare_semantic_corpus as corpus
import verify_cocoindex_wheel as wheel
from _catalog_publication import checked_path
from prepare_cocoindex_source import INPUTS, ROOT
from prepare_crawl4ai_source import digest, files, runtime_sources


def write_json(path: Path, value: Any, *, new: bool = False) -> None:
    with path.open("x" if new else "w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def admit_runtime(home: Path) -> dict[str, Any]:
    home = corpus.checked_output(ROOT, home)
    if Path(sys.prefix).resolve() != checked_path(home, "runtime").resolve():
        raise ValueError("Run this worker only in its owned provider runtime")
    pin = json.loads((ROOT / INPUTS / "source.json").read_bytes())
    count = wheel.installed_files(pin)
    return {"provider_version": pin["version"], "source_files_admitted": count}


def model_proof() -> dict[str, Any]:
    proof = json.loads((ROOT / INPUTS / "model.json").read_bytes())
    if isinstance(proof["files"], list):
        proof["files"] = runtime_sources({"runtime_files": proof["files"]})
    if proof.get("custom_code_present") is not False:
        raise ValueError("The local model proof must exclude custom model code")
    modules = proof.get("modules")
    expected = ["sentence_transformers.models." + name for name in ["Transformer", "Pooling", "Normalize"]]
    if (
        not isinstance(modules, list)
        or not all(isinstance(module, dict) for module in modules)
        or [module.get("type") for module in modules] != expected
    ):
        raise ValueError("The qualified local model supports only its three pinned built-in modules")
    if "model.safetensors" not in proof["files"] or any(
        not name.lower().endswith((".json", ".txt", ".md", ".safetensors")) for name in proof["files"]
    ):
        raise ValueError("The qualified model requires safe tensor weights and non-executable supporting files")
    return proof


def check_model(home: Path) -> dict[str, Any]:
    proof = model_proof()
    model = checked_path(home, "model")
    actual = files(model)
    if set(actual) != set(proof["files"]):
        raise ValueError("Local embedding model inventory differs from its exact source pin")
    errors = []
    for name, expected in proof["files"].items():
        try:
            size = corpus.regular_file(model, name).stat().st_size
            if actual[name] != expected or size != proof["file_sizes"][name]:
                errors.append("changed model file: " + name)
        except (OSError, ValueError) as error:
            errors.append(f"invalid model file {name}: {error}")
    if errors:
        raise ValueError("; ".join(errors))
    if json.loads((model / "modules.json").read_bytes()) != proof["modules"]:
        raise ValueError("Local model module declarations differ from the built-in-only source pin")
    return {"model_files_admitted": len(proof["files"]), "model_revision": proof["revision"]}


def install_model(home: Path) -> dict[str, Any]:
    from huggingface_hub import get_hf_file_metadata, hf_hub_download, hf_hub_url

    proof = model_proof()
    download = checked_path(home, "model-download")
    model = checked_path(home, "model")
    model.mkdir(exist_ok=False)
    records = []
    for name, expected in proof["files"].items():
        url = hf_hub_url(proof["model"], name, revision=proof["revision"])
        metadata = get_hf_file_metadata(url, token=False, timeout=30, retry_on_errors=False)
        if metadata.commit_hash != proof["revision"] or metadata.size != proof["file_sizes"][name]:
            raise ValueError("Model artifact metadata differs from its pinned revision or size: " + name)
        downloaded = Path(
            hf_hub_download(
                proof["model"], name, revision=proof["revision"], local_dir=download, token=False, etag_timeout=30
            )
        )
        original = corpus.regular_file(download, name)
        observed, size = corpus.fingerprint(original)
        if downloaded.resolve() != original.resolve() or observed != expected or size != proof["file_sizes"][name]:
            raise ValueError("Downloaded model artifact differs from pinned bytes: " + name)
        target = checked_path(model, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(original, target)
        records.append(
            {
                "path": name,
                "url": url,
                "sha256": observed,
                "bytes": size,
                "native_metadata_commit": metadata.commit_hash,
                "native_metadata_etag": metadata.etag,
                "native_status_exposed": False,
            }
        )
        write_json(
            home / "model-download.json",
            {
                "model": proof["model"],
                "revision": proof["revision"],
                "files": records,
                "personal_token_used": False,
                "external_llm": False,
            },
        )
    return check_model(home)


def corpus_path(home: Path, base: Path) -> Path:
    base = corpus.checked_output(ROOT, base)
    if base == ROOT / ".venv" or base.is_relative_to(home) or home.is_relative_to(base):
        raise ValueError("Select a dedicated corpus outside the provider home")
    return base


def configurations(home: Path) -> dict[str, dict[str, Any]]:
    return {
        "config/global_settings.yml": {
            "daemon": {"idle_timeout_minutes": 1, "keep_alive_with_mcp": False},
            "embedding": {
                "device": "cpu",
                "provider": "sentence-transformers",
                "model": str(home / "model"),
                "indexing_params": {},
                "query_params": {"prompt_name": "query"},
            },
        },
        "tree/.cocoindex_code/settings.yml": {
            "exclude_patterns": [".cocoindex_code/**"],
            "include_patterns": ["**/*"],
            "max_file_size": corpus.MAX_FILE_BYTES,
        },
    }


def configure(home: Path, base: Path, *, check: bool) -> None:
    for name, value in configurations(home).items():
        path = checked_path(base, name)
        if not check:
            path.parent.mkdir(parents=True, exist_ok=True)
            write_json(path, value, new=True)
        if json.loads(corpus.regular_file(base, name).read_bytes()) != value:
            raise ValueError("Corpus configuration differs from its isolated local-only contract: " + name)


def local_environment(home: Path, base: Path) -> dict[str, str]:
    import search_semantic_corpus as search

    providers = checked_path(home, "runtime/Lib/site-packages")
    checked_path(base, "runtime")
    return search.local_environment(ROOT, base, Path(sys.executable), providers, ROOT / INPUTS / "model.json")


def wait_for_index(project_root: Path, *, timeout: float = 500) -> dict[str, Any]:
    import msgspec
    from cocoindex_code.client import project_status

    deadline = time.monotonic() + timeout
    while True:
        status = msgspec.to_builtins(project_status(str(project_root)))
        if not status["indexing"]:
            break
        if time.monotonic() >= deadline:
            raise TimeoutError("The provider did not finish its native startup scan within the index-check deadline")
        time.sleep(0.1)
    if not status["index_exists"] or (status.get("progress") or {}).get("num_errors", 0):
        raise ValueError("The provider has no completed error-free index")
    return status


def index(home: Path, base: Path, prefixes: list[str], *, check: bool) -> dict[str, Any]:
    base = corpus_path(home, base)
    existing = base.exists()
    if check and not existing:
        raise ValueError("The corpus must already exist for an index check")
    prepared = corpus.prepare(ROOT, base, prefixes, check=existing)
    if not prepared["ok"]:
        raise ValueError("Stale corpus; preserve its evidence and select a new path: " + "; ".join(prepared["errors"]))
    configure(home, base, check=existing)
    env = local_environment(home, base)
    status = None
    if check:
        previous = dict(os.environ)
        try:
            os.environ.clear()
            os.environ.update(env)
            status = wait_for_index(base / "tree")
        finally:
            os.environ.clear()
            os.environ.update(previous)
    else:
        command = [sys.executable, "-P", "-c", "from cocoindex_code.cli import app;app()", "index"]
        subprocess.run(command, cwd=base / "tree", env=env, check=True, timeout=540)
    after = corpus.prepare(ROOT, base, prefixes, check=True)
    if not after["ok"]:
        raise ValueError("Source binding changed during indexing: " + "; ".join(after["errors"]))
    result = {
        **prepared,
        "corpus": str(base),
        "manifest_sha256": digest((base / "manifest.json").read_bytes()),
        "model_revision": model_proof()["revision"],
        "agent_efficacy_scored": False,
    }
    if status is not None:
        result["native_index_status"] = status
    if not check:
        write_json(base / "index-receipt.json", result)
    return result


def query(home: Path, args: argparse.Namespace) -> int:
    import search_semantic_corpus as search

    base = corpus_path(home, args.corpus)
    configure(home, base, check=True)
    output = corpus.checked_output(ROOT, args.output)
    if output.exists() or output.is_relative_to(home) or output.is_relative_to(base):
        raise ValueError("Select a new query receipt outside provider and corpus caches")
    output.parent.mkdir(parents=True, exist_ok=True)
    arguments = [
        "--root",
        str(ROOT),
        "--corpus",
        str(base),
        "--python",
        sys.executable,
        "--provider-dir",
        str(checked_path(home, "runtime/Lib/site-packages")),
        "--model-proof",
        str(ROOT / INPUTS / "model.json"),
        "--query",
        args.query,
        "--limit",
        str(args.limit),
        "--json",
    ]
    for pattern in args.path:
        arguments.extend(["--path", pattern])
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        status = search.main(arguments)
    raw = stdout.getvalue().encode("utf-8")
    with output.open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"ok": status == 0, "output": str(output), "sha256": digest(raw)}))
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("check-runtime")
    commands.add_parser("install-model")
    commands.add_parser("check-model")
    prepare = commands.add_parser("index")
    prepare.add_argument("--corpus", type=Path, required=True)
    prepare.add_argument("--prefix", action="append", required=True)
    prepare.add_argument("--check", action="store_true")
    retrieve = commands.add_parser("query")
    retrieve.add_argument("--corpus", type=Path, required=True)
    retrieve.add_argument("--query", required=True)
    retrieve.add_argument("--path", action="append", default=[])
    retrieve.add_argument("--limit", type=int, choices=range(1, 21), default=5)
    retrieve.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        home = corpus.checked_output(ROOT, args.home)
        result = admit_runtime(home)
        if args.command == "install-model":
            result.update(install_model(home))
        elif args.command != "check-runtime":
            result.update(check_model(home))
            if args.command == "index":
                result.update(index(home, args.corpus, args.prefix, check=args.check))
            elif args.command == "query":
                return query(home, args)
        result["ok"] = True
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        importlib.metadata.PackageNotFoundError,
    ) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())
