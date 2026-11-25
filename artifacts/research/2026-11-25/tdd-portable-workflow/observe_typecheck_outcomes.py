"""Check a real type-check regression and separate compiler setup errors."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

node, evidence, output = (Path(arg).resolve() for arg in sys.argv[1:])
assert platform.machine().lower() in {"amd64", "x86_64"} and sys.platform in {"win32", "linux"}
system = sys.platform
base = json.loads((evidence / "typescript-latest.native.json").read_bytes())
native = json.loads((evidence / f"typescript-{system}-x64.native.json").read_bytes())
assert base["version"] == native["version"] == "7.0.2"
assert base["dependencies"][native["name"]] == native["version"]
output.mkdir()

with tempfile.TemporaryDirectory(prefix="typescript-outcome-control-") as work:
    root = Path(work)
    modules = root / "node_modules"
    assets = {}
    for package in (base, native):
        name = package["name"]
        location = modules / name
        assert location.resolve().is_relative_to(modules.resolve())
        location.mkdir(parents=True)
        with urllib.request.urlopen(package["dist"]["tarball"], timeout=20) as response:
            raw = response.read(32 * 1024**2 + 1)
        if len(raw) > 32 * 1024**2:
            raise ValueError("Archive exceeded the declared byte limit")
        sri = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode()
        if sri != package["dist"]["integrity"]:
            raise ValueError("The official npm archive did not match its declared digest")
        assets[name] = {"sha512": sri, "archive_bytes": len(raw)}
        archive_path = root / f"package-{len(assets)}.tgz"
        archive_path.write_bytes(raw)
        with tarfile.open(archive_path, "r:gz") as archive:
            entries = []
            for item in archive:
                member = PurePosixPath(item.name)
                assert member.parts[0] == "package" and len(member.parts) > 1
                assert item.isfile() and not member.is_absolute() and ".." not in member.parts
                entries.append(item.replace(name=PurePosixPath(*member.parts[1:]).as_posix()))
            archive.extractall(location, members=entries, filter="data")
    main = modules / "typescript" / base["bin"]["tsc"]
    runtime_hash = hashlib.sha256(node.read_bytes()).hexdigest()
    expected_node_hash = {
        "win32": "86fc4785327db5f5c7558dc6156c543b433c313e813a222e088086222ab4afa6",
        "linux": "a7ec1b37e6ff9d187e4198c5b6df9a4eb1c74dd31804fb3bac55cc4ceca1ac01",
    }
    assert runtime_hash == expected_node_hash[system]
    scratch_env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC") if key in os.environ}
    scratch_env.update(
        PATH=str(node.parent), HOME=str(root), USERPROFILE=str(root),
        APPDATA=str(root), LOCALAPPDATA=str(root), TEMP=str(root), TMP=str(root), TMPDIR=str(root),
    )

    def call(label, args):
        result = subprocess.run(
            args, cwd=root, env=scratch_env, stdin=subprocess.DEVNULL, capture_output=True, timeout=25
        )
        (output / f"{label}.stdout.native").write_bytes(result.stdout)
        (output / f"{label}.stderr.native").write_bytes(result.stderr)
        return result

    version = call("node-version", [node, "--version"])
    assert version.returncode == 0 and version.stdout.strip() == b"v24.22.3"
    version = call("compiler-version", [node, main, "--version"])
    assert version.returncode == 0 and version.stdout.strip() == b"Version 7.0.2"
    customer = root / "consumer.ts"
    customer.write_bytes(b'import { label } from "./contract";\nconst result: string = label("ready");\n')
    (root / "tsconfig.json").write_text(json.dumps({
        "compilerOptions": {"noEmit": True, "strict": True, "target": "ES2022", "module": "ESNext"},
        "files": ["consumer.ts", "contract.ts"],
    }), encoding="utf-8")
    check = [node, main, "--project", "tsconfig.json", "--pretty", "false"]
    entries = {}
    for name, signature, extra, needle in (
        ("type-contract-fails", "number", [], b"error TS2345"),
        ("type-contract-passes", "string | number", [], b""),
        ("invalid-runner-option", "string | number", ["--nonexistentSetupSwitch"], b"error TS5023"),
    ):
        implementation = root / "contract.ts"
        implementation.write_bytes(f"export function label(value: {signature}): string {{ return String(value); }}\n".encode())
        result = call(name, [*check, *extra])
        content = result.stdout + result.stderr
        assert (result.returncode != 0) == bool(needle)
        if needle:
            assert needle in content
        if name == "type-contract-fails":
            assert b"consumer.ts(2," in content
        if name == "type-contract-passes":
            assert not content.strip()
        entries[name] = {
            "exit_code": result.returncode,
            "diagnostic": needle.decode(),
            "consumer_sha256": hashlib.sha256(customer.read_bytes()).hexdigest(),
            "implementation_sha256": hashlib.sha256(implementation.read_bytes()).hexdigest(),
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        }
    assert len({row["consumer_sha256"] for row in entries.values()}) == 1
path = output / "result.json"
path.write_text(json.dumps({
    "typescript": base["version"], "node": "24.22.3", "platform": system, "packages": assets,
    "cases": entries, "scratch_removed": not root.exists(), "model_attempts": 0,
}, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"platform": system, "cases": len(entries), "passed": True}))
