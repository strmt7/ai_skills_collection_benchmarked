"""Exercise the pinned TypeScript fallback and a one-option diagnostic copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

EXTRACTOR_SHA256 = "c286bc17ab3d90ea5e471539149e523fcefe0d6f7fbf0dcfbdf34087f532495d"
MANIFEST_SHA256 = "74a65805009f1f9164dfea5bd80b37b93c1cf494928f7fd62c2851c84c609c57"
LOCK_SHA256 = "0219a1c50383072beeb9250cce4ced3a6bb3210b868e1ff5d77a14e3d0a887be"
VERSIONS = {"ts-morph": "21.0.1", "typescript": "5.9.3", "ts-node": "10.9.2", "@types/node": "20.19.43"}
FIXTURE = {
    "package.json": '{"name":"fixture","dependencies":{"next":"fixture"}}',
    "app/api/ping/route.ts": 'export function GET() { return new Response("ping"); }',
    "app/products/route.ts": 'export function GET() { return new Response("products"); }',
    "src/cache.ts": 'const cache = new Map<string, string>(); cache.get("cache-key");',
    "src/server.js": 'app.get("/health", handler);',
}


def pinned(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, type=Path)
    parser.add_argument("--extractor", required=True, type=Path)
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    provider = args.provider.resolve()
    source = pinned(args.extractor, EXTRACTOR_SHA256)
    pinned(provider / "package.json", MANIFEST_SHA256)
    pinned(provider / "package-lock.json", LOCK_SHA256)
    for package, expected in VERSIONS.items():
        info = json.loads((provider / "node_modules" / package / "package.json").read_text(encoding="utf-8"))
        if info["version"] != expected:
            raise ValueError(f"Unexpected installed version: {package}")
    node = subprocess.run(
        [args.node, "--version"], capture_output=True, text=True, check=True, timeout=30
    ).stdout.strip()
    launcher = provider / "node_modules" / "ts-node" / "dist" / "bin.js"
    env = {key: value for key, value in os.environ.items() if not key.startswith("TS_NODE_")}
    env.pop("NODE_OPTIONS", None)
    env.pop("NODE_PATH", None)
    with tempfile.TemporaryDirectory(prefix="docs-extractor-control-", dir=provider) as temporary:
        root = Path(temporary)
        fixture = root / "fixture"
        for name, text in FIXTURE.items():
            path = fixture / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        original = root / "original.ts"
        original.write_bytes(source)
        output = root / "original.json"
        command = [args.node, str(launcher), str(original), str(fixture), str(output)]
        first = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60, env=env)
        if first.returncode == 0 or "TS2353" not in first.stderr or output.exists():
            raise ValueError("The original startup failure did not reproduce")
        old, new = b"addFilesFromTsConfig: false", b"skipAddingFilesFromTsConfig: true"
        if source.count(old) != 1:
            raise ValueError("Unexpected diagnostic patch target")
        diagnostic = root / "diagnostic.ts"
        diagnostic.write_bytes(source.replace(old, new))
        output = root / "diagnostic.json"
        second = subprocess.run(
            [args.node, str(launcher), str(diagnostic), str(fixture), str(output)],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            env=env,
        )
        if second.returncode != 0 or not output.is_file():
            raise ValueError("Diagnostic copy did not run")
        metadata = json.loads(output.read_text(encoding="utf-8"))
        routes = sorted((route["method"], route["path"]) for route in metadata["routes"])
        if routes != [("GET", "/api/ping"), ("GET", "cache-key")]:
            raise ValueError(f"Unexpected diagnostic routes: {routes}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "node": node,
                "extractor_sha256": EXTRACTOR_SHA256,
                "manifest_sha256": MANIFEST_SHA256,
                "qualification_lock_sha256": LOCK_SHA256,
                "installed_versions": VERSIONS,
                "original_exit_code": first.returncode,
                "original_diagnostic": "TS2353",
                "diagnostic_copy_replaced_only_project_option": True,
                "diagnostic_exit_code": second.returncode,
                "diagnostic_routes": routes,
                "fixture_executed": False,
                "agent_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
