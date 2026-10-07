#!/usr/bin/env python3
"""Query a fresh local CocoIndex corpus and verify every returned source span."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Any

import prepare_semantic_corpus as corpus
import yaml

ROOT = Path(__file__).resolve().parents[1]
CLIENT = """import importlib.metadata,json,sys,msgspec
from cocoindex_code.client import search,project_status,daemon_status
request=json.load(sys.stdin)
response=search(**request)
print(json.dumps({'response':msgspec.to_builtins(response),
                  'project_status':msgspec.to_builtins(project_status(request['project_root'])),
                  'daemon_status':msgspec.to_builtins(daemon_status()),
                  'versions':{name:importlib.metadata.version(name) for name in ('cocoindex','cocoindex-code')},
                  'python_version':sys.version.split()[0]}))
"""


def verify_response(
    response: dict[str, Any], base: Path, manifest: dict[str, Any], paths: list[str], limit: int
) -> list[dict[str, Any]]:
    """Validate provider data independently against the exact indexed source."""
    hits = response.get("results")
    if response.get("success") is not True or not isinstance(hits, list) or not hits or len(hits) > limit:
        raise ValueError("search failed, returned no hits, or exceeded the limit")
    if (
        type(response.get("total_returned")) is not int
        or type(response.get("offset")) is not int
        or response["total_returned"] != len(hits)
        or response["offset"] != 0
    ):
        raise ValueError("inconsistent search counts or offset")
    checks = []
    with closing(sqlite3.connect(":memory:")) as matcher:
        for hit in hits:
            if (
                not isinstance(hit, dict)
                or not isinstance(hit.get("file_path"), str)
                or not isinstance(hit.get("content"), str)
            ):
                raise ValueError("malformed search hit")
            name = hit["file_path"]
            if name not in manifest["files"] or manifest["files"][name]["excluded_reason"] is not None:
                raise ValueError("result is outside the selected text corpus")
            if paths and not any(
                matcher.execute("SELECT ? GLOB ?", (name, pattern)).fetchone()[0] for pattern in paths
            ):
                raise ValueError("result is outside the requested path scope")
            raw = corpus.regular_file(base / "tree", name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != manifest["files"][name]["sha256"]:
                raise ValueError("retrieved file differs from its source binding")
            lines = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").splitlines()
            start, end = hit["start_line"], hit["end_line"]
            if any(type(value) is not int for value in (start, end)) or not 1 <= start <= end <= len(lines):
                raise ValueError("invalid one-based source coordinates")
            content = hit["content"].replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")
            if not content or content not in "\n".join(lines[start - 1 : end]):
                raise ValueError("retrieved content differs from its source span")
            if type(hit["score"]) not in (float, int) or not math.isfinite(hit["score"]):
                raise ValueError("nonfinite or invalid similarity score")
            checks.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "source_span_verified": True})
    return checks


def local_environment(root: Path, base: Path, python: Path, providers: Path, proof: Path) -> dict[str, str]:
    """Bind an explicitly selected CPU provider and local model without installation."""
    for path in (python, providers):
        corpus.checked_output(root, path)
    corpus.regular_file(root, python.relative_to(root).as_posix())
    settings = yaml.safe_load(corpus.regular_file(base, "config/global_settings.yml").read_text(encoding="utf-8"))
    embedding = settings["embedding"]
    model = Path(embedding["model"]).resolve(strict=True)
    corpus.checked_output(root, model)
    if embedding.get("provider") != "sentence-transformers" or embedding.get("device") != "cpu":
        raise ValueError("only the explicitly configured local CPU model is qualified")
    if not providers.is_dir():
        raise ValueError("provider directory is missing")
    proof_raw = corpus.regular_file(root, proof.relative_to(root).as_posix()).read_bytes()
    model_proof = json.loads(proof_raw)
    if model_proof.get("custom_code_present") is not False:
        raise ValueError("model proof must exclude custom code")
    expected = model_proof["files"]
    if {p.relative_to(model).as_posix() for p in model.rglob("*") if p.is_file()} != set(expected):
        raise ValueError("local model inventory differs from the pinned proof")
    for name, digest in expected.items():
        if hashlib.sha256(corpus.regular_file(model, name).read_bytes()).hexdigest() != digest:
            raise ValueError("local model differs from the pinned proof")
    env = {key: value for key, value in os.environ.items() if not key.startswith("COCOINDEX_")}
    env.update(
        PYTHONPATH=str(providers),
        COCOINDEX_CODE_DIR=str(base / "config"),
        COCOINDEX_CODE_RUNTIME_DIR=str(base / "runtime"),
        COCOINDEX_DISABLE_USAGE_TRACKING="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        TOKENIZERS_PARALLELISM="false",
    )
    return env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--provider-dir", type=Path, required=True)
    parser.add_argument("--model-proof", type=Path, required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--limit", type=int, choices=range(1, 21), default=3)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        base = corpus.checked_output(root, args.corpus)
        manifest_raw = corpus.regular_file(base, "manifest.json").read_bytes()
        manifest = json.loads(manifest_raw)
        before = corpus.prepare(root, base, manifest["prefixes"], check=True)
        if not before["ok"]:
            raise ValueError("stale corpus: " + "; ".join(before["errors"]))
        python = args.python.resolve(strict=True)
        env = local_environment(
            root,
            base,
            python,
            args.provider_dir.resolve(strict=True),
            args.model_proof.resolve(strict=True),
        )
        request = {
            "project_root": str(base / "tree"),
            "query": args.query,
            "paths": args.path or None,
            "limit": args.limit,
            "offset": 0,
        }
        result = subprocess.run(
            [str(python), "-c", CLIENT],
            input=json.dumps(request),
            env=env,
            cwd=base / "tree",
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
            check=True,
        )
        report = json.loads(result.stdout)
        checks = verify_response(report["response"], base, manifest, args.path, args.limit)
        after = corpus.prepare(root, base, manifest["prefixes"], check=True)
        if not after["ok"] or corpus.regular_file(base, "manifest.json").read_bytes() != manifest_raw:
            raise ValueError("source binding changed during retrieval")
        if (
            report["project_status"].get("indexing") is not False
            or report["project_status"].get("index_exists") is not True
        ):
            raise ValueError("index is missing or still changing")
        report.update(
            ok=True,
            source_checks=checks,
            manifest_sha256=hashlib.sha256(manifest_raw).hexdigest(),
            query=request,
            stderr=result.stderr,
            retrieval_quality_established=False,
            agent_efficacy_scored=False,
        )
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        report = {"ok": False, "errors": [str(exc)]}
    print(
        json.dumps(report, indent=2)
        if args.json
        else ("OK: source-verified semantic hits" if report["ok"] else "ERROR: " + "; ".join(report["errors"]))
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
