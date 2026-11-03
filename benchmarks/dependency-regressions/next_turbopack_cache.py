"""Check version-bound Next.js Turbopack default configuration exports."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

PACKAGES = {
    "16.0.0": (
        "nYohiNdxGu4OmBzggxy9rczmjIGI+TpR5vbKTsE1HqYwNm1B+YSiugSrFguX6omMOKnDHAmBPY4+8TNJk0Idyg==",
        "8c3d63a8085c068f0c89a2e3e2913f8d79624ff2712a8143102347321e41dbc3",
        (False, None, False, None),
    ),
    "16.1.0": (
        "Y+KbmDbefYtHDDQKLNrmzE/YYzG2msqo2VXhzh5yrJ54tx/6TmGdkR5+kP9ma7i7LwZpZMfoY3m/AoPPPKxtVw==",
        "a9e1d6fd8e6f34e0d03af458d8903f9c5c0a44ccac331fa93e9f39c59d9bfd31",
        (True, True, True, False),
    ),
    "16.3.0": (
        "NEdGOzH+08eTXMUp9UYkA99Nhi5N6Thrhc1jgFOQgfgnGK/dA2hRwBpXep+exdFQrnwlRf/3Wixyp8lLBUpE2A==",
        "2c15353ce27ba7ea7322b53f3194c6d39593936f2c73e303cbd2dd7d37d88f0a",
        (True, True, True, True),
    ),
    "16.4.4": (
        "Hu4pOw2x0RQ0TQabNWbpsNg/3+SZf+rLQwvfhBLnptv98GS4dcIVMlfEyn9jb2/ZJDSahhnUKEs0YrfarjGX3A==",
        "cc8b6197fd97a12b0d9257c9d7d4288347053fc8712b021d03c3bfad7a19cdd3",
        (True, True, True, True),
    ),
}

MEMBERS = (
    "package/package.json",
    "package/LICENSE",
    "package/dist/server/config-shared.js",
    "package/dist/shared/lib/image-config.js",
    "package/dist/lib/constants.js",
    "package/dist/shared/lib/errors/canary-only-config-error.js",
    "package/dist/shared/lib/size-limit.js",
    "package/dist/compiled/bytes/index.js",
    "package/dist/compiled/bytes/package.json",
    "package/dist/compiled/bytes/LICENSE",
)

NODE_PROBE = r"""
const fs = require('fs');
const path = require('path');
const root = fs.realpathSync(process.env.CONTROL_ROOT);
const config = require(process.env.CONTROL_CONFIG).defaultConfig.experimental;
const defaults = {};
for (const key of ['turbopackFileSystemCacheForDev', 'turbopackFileSystemCacheForBuild']) {
  defaults[key] = {present: Object.hasOwn(config, key), value: config[key] === undefined ? null : config[key]};
}
const modules = Object.keys(require.cache).map(file => {
  const rel = path.relative(root, fs.realpathSync(file));
  if (!rel || path.isAbsolute(rel) || rel === '..' || rel.startsWith('..' + path.sep)) {
    throw new Error('module resolved outside the isolated fixture');
  }
  return rel.split(path.sep).join('/');
}).sort();
process.stdout.write(JSON.stringify({defaults, modules}));
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", type=Path, help="Directory containing the four pinned npm archives")
    parser.add_argument("--node", default="node", help="Node.js executable")
    parser.add_argument("--output", type=Path, required=True, help="New result file, or recorded file with --check")
    parser.add_argument("--check", action="store_true", help="Validate recorded evidence without executing Node.js")
    return parser


def digest(path: Path, algorithm: str) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def expected_defaults(version: str) -> dict[str, dict[str, object]]:
    dev_present, dev, build_present, build = PACKAGES[version][2]
    return {
        "turbopackFileSystemCacheForDev": {"present": dev_present, "value": dev},
        "turbopackFileSystemCacheForBuild": {"present": build_present, "value": build},
    }


def defaults_match(version: str, observed: object) -> bool:
    expected = expected_defaults(version)
    if not isinstance(observed, dict) or set(observed) != set(expected):
        return False
    for name, expected_value in expected.items():
        item = observed[name]
        if (
            not isinstance(item, dict)
            or set(item) != {"present", "value"}
            or type(item["present"]) is not bool
            or item["present"] is not expected_value["present"]
            or item["value"] is not expected_value["value"]
        ):
            return False
    return True


def check_record(path: Path) -> list[str]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read result: {type(exc).__name__}"]
    if not isinstance(record, dict):
        return ["result must be an object"]
    errors = []
    if (
        type(record.get("schema_version")) is not int
        or record.get("schema_version") != 1
        or record.get("evidence_class") != "next-turbopack-cache-config-controls"
        or record.get("passed") is not True
        or record.get("errors") != []
        or record.get("reproducer_sha256") != digest(Path(__file__), "sha256")
        or not isinstance(record.get("node_version"), str)
        or not record["node_version"]
        or not isinstance(record.get("node_sha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", record["node_sha256"])
    ):
        errors.append("invalid status, runtime or control-source identity")
    versions = record.get("versions")
    if not isinstance(versions, dict) or set(versions) != set(PACKAGES):
        return [*errors, "all four package results are required"]
    for version, (integrity, config_sha, _) in PACKAGES.items():
        item = versions[version]
        if (
            not isinstance(item, dict)
            or item.get("archive_integrity") != f"sha512-{integrity}"
            or item.get("config_sha256") != config_sha
            or not defaults_match(version, item.get("defaults"))
            or not isinstance(item.get("modules"), list)
            or not item["modules"]
            or any(
                not isinstance(p, str)
                or not p.startswith("node_modules/next/")
                or ".." in PurePosixPath(p).parts
                or PurePosixPath(p).as_posix() != p
                for p in item["modules"]
            )
        ):
            errors.append(f"{version}: invalid package evidence or observed defaults")
    return errors


def inspect_package(version: str, archive: Path, node: str, work: Path) -> dict[str, object]:
    integrity, config_sha, _ = PACKAGES[version]
    expected = base64.b64decode(integrity, validate=True).hex()
    if digest(archive, "sha512") != expected:
        raise ValueError(f"{version}: npm archive digest mismatch")
    fixture = work / version
    package = fixture / "node_modules/next"
    with tarfile.open(archive, "r:gz") as tar:
        selected = {}
        for member in tar:
            if member.name in MEMBERS:
                if member.name in selected or not member.isfile() or member.size > 2_000_000:
                    raise ValueError(f"{version}: invalid package member")
                selected[member.name] = member
        for name, member in selected.items():
            destination = package.joinpath(*PurePosixPath(name).relative_to("package").parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = tar.extractfile(member)
            if source is None:
                raise ValueError(f"{version}: unreadable package member")
            destination.write_bytes(source.read())
    config = package / "dist/server/config-shared.js"
    if (
        digest(config, "sha256") != config_sha
        or json.loads((package / "package.json").read_text(encoding="utf-8"))["version"] != version
    ):
        raise ValueError(f"{version}: package identity mismatch")
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("NODE_", "NEXT_", "__NEXT_", "NPM_"))}
    env.update(CONTROL_ROOT=str(fixture.resolve()), CONTROL_CONFIG=str(config.resolve()))
    run = subprocess.run(
        [node, "--max-old-space-size=128", "-e", NODE_PROBE],
        cwd=fixture,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    if run.returncode or run.stderr:
        raise ValueError(f"{version}: Node probe failed: {run.stderr[-1000:]}")
    observed = json.loads(run.stdout)
    if not defaults_match(version, observed.get("defaults")):
        raise ValueError(f"{version}: unexpected default configuration")
    return {"archive_integrity": f"sha512-{integrity}", "config_sha256": config_sha, **observed}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        errors = check_record(args.output)
        print(json.dumps({"valid": not errors, "errors": errors}, sort_keys=True))
        return 0 if not errors else 1
    try:
        if args.archives is None or args.output.exists():
            raise ValueError("provide an archive directory and a new output path")
        node = shutil.which(args.node)
        if node is None:
            raise ValueError("Node.js executable is unavailable")
        node = str(Path(node).resolve(strict=True))
        version = subprocess.run(
            [node, "--version"], capture_output=True, text=True, timeout=30, check=True
        ).stdout.strip()
        with tempfile.TemporaryDirectory(prefix="next-cache-control-") as temporary:
            work = Path(temporary)
            versions = {v: inspect_package(v, args.archives / f"next-{v}.tgz", node, work) for v in PACKAGES}
        report = {
            "schema_version": 1,
            "evidence_class": "next-turbopack-cache-config-controls",
            "scope": "Selected package configuration exports only; no server, build, cache persistence or performance measurement.",
            "platform": platform.system(),
            "node_version": version,
            "node_sha256": digest(Path(node), "sha256"),
            "reproducer_sha256": digest(Path(__file__), "sha256"),
            "versions": versions,
            "errors": [],
            "passed": True,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, indent=2, sort_keys=True)
            stream.write("\n")
    except (OSError, ValueError, KeyError, tarfile.TarError, subprocess.SubprocessError) as exc:
        print(json.dumps({"passed": False, "errors": [f"{type(exc).__name__}: {exc}"]}, sort_keys=True))
        return 1
    print(json.dumps({"passed": True, "versions": list(versions)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
