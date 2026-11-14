#!/usr/bin/env python3
"""Build and qualify a pinned modern Node replay without a persistent build service."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import shutil
import sys
import tarfile
from pathlib import Path
from typing import Any

from _bootstrap_archive import ordinary
from _native_benchmark_runtime import ContainerLease, DockerClient, LeaseResources, write_json
from _native_image_archive import validate_image_archive
from _native_replay_assets import admit_crane, download, file_sha256, node_layer, remove_owned_tag
from _trial_transcript import strict_json
from _windows_trial_process import run_owned
from grade_swe_skills_submission import source_hashes

ROOT = Path(__file__).resolve().parents[1]
PIN_DIRECTORY = "toolchains/native-node-replay"
PATH_VALUE = "/opt/benchmark-node/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


def implementation(root: Path) -> dict[str, str]:
    names = ["tools/prepare_native_node_replay.py", "tools/_native_replay_assets.py"]
    names.extend(PIN_DIRECTORY + "/" + name for name in ("pins.json", "base-manifest.json", "base-config.json"))
    return {**source_hashes(), **{name: file_sha256(root / name) for name in names}}


def native_phase(output: Path, argv: list[str], environment: dict[str, str]) -> dict[str, Any]:
    with (
        (output / "crane.stdout.native").open("xb") as stdout,
        (output / "crane.stderr.native").open("xb") as stderr,
        open(os.devnull, "rb") as stdin,
    ):
        result = run_owned(
            argv,
            cwd=output,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=360,
            output_limit=2 * 1024**2,
            memory_limit=512 * 1024**2,
            process_limit=8,
            environment=environment,
        )
    write_json(output / "crane-process.json", {"argv": argv, "process": result})
    if result["exit_code"] or result["termination_reason"] or result["job_active_processes_after_cleanup"]:
        raise RuntimeError("Image assembly failed; retained native output and process receipt")
    return result


def runtime_probes(client: DockerClient, output: Path, pin: dict[str, Any]) -> list[dict[str, str]]:
    lease = ContainerLease(
        client, output / "probe.lease.json", seconds=120, resources=LeaseResources(memory_bytes=512 * 1024**2)
    )
    results = []
    try:
        identity = lease.create()
        lease.start()
        program = (
            "const a=require('node:assert/strict');const c=require('node:crypto');"
            "a.equal(process.platform,'linux');a.equal(process.arch,'x64');"
            "a.equal(c.createHash('sha256').update('abc').digest('hex'),"
            "'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');"
            "console.log(process.version)"
        )
        for name, command, expected in (
            ("node", ["node", "--eval", program], pin["version"]),
            ("npm", ["npm", "--version"], pin["npm_version"]),
            ("npx", ["npx", "--version"], pin["npm_version"]),
        ):
            raw = client.run(
                "probe-" + name,
                ["container", "exec", "--user=1001:1001", "--workdir=/tmp", "--env=HOME=/tmp", identity, *command],
                timeout=25,
            )
            observed = raw.decode("utf-8").strip()
            if observed != expected:
                raise ValueError("Replay probe returned an unexpected " + name + " version")
            results.append({"tool": name, "version": observed})
    finally:
        lease.close()
    if client.ids(lease.token):
        raise RuntimeError("Replay probe container remains")
    return results


def prepare(root: Path, runtime: Path, output: Path) -> dict[str, Any]:
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise ValueError("Replay setup requires Windows x64 and a qualified local Linux AMD64 engine")
    output = output.resolve()
    ordinary(output)
    if not output.is_relative_to(root / ".venv"):
        raise ValueError("Replay output must stay inside this checkout's .venv")
    output.mkdir(parents=True)
    try:
        return assemble(root, runtime, output)
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, tarfile.TarError) as error:
        write_json(
            output / "failure.json",
            {"passed": False, "error_type": type(error).__name__, "errors": [str(error)], "model_invocations": 0},
        )
        raise


def assemble(root: Path, runtime: Path, output: Path) -> dict[str, Any]:
    sources = implementation(root)
    snapshot_directory = output / "implementation"
    snapshot_directory.mkdir()
    snapshots = []
    for index, (name, digest) in enumerate(sorted(sources.items())):
        snapshot = snapshot_directory / (str(index).zfill(3) + ".txt")
        with snapshot.open("xb") as writer:
            writer.write((root / name).read_bytes())
        if file_sha256(snapshot) != digest:
            raise ValueError("Replay source changed during provenance capture")
        snapshots.append({"source_path": name, "snapshot": snapshot.name, "sha256": digest})
    write_json(snapshot_directory / "manifest.json", snapshots)
    pin_dir = root / PIN_DIRECTORY
    pin = strict_json((pin_dir / "pins.json").read_text(encoding="utf-8"))
    supplied = strict_json(runtime.read_text(encoding="utf-8"))
    if (
        pin["schema_version"] != 1
        or supplied["schema_version"] != 1
        or supplied["image_reference"] != pin["base_image_reference"]
    ):
        raise ValueError("Replay requires the pinned publisher base runtime")
    for name, expected in (
        ("base-manifest.json", pin["base_manifest_sha256"]),
        ("base-config.json", pin["base_config_sha256"]),
    ):
        if file_sha256(pin_dir / name) != expected:
            raise ValueError("Replay base metadata differs from its pin")
    if file_sha256(Path(supplied["image_manifest"])) != pin["base_manifest_sha256"]:
        raise ValueError("Supplied publisher manifest differs from the replay base")
    base = strict_json((pin_dir / "base-config.json").read_text(encoding="utf-8"))
    manifest = strict_json((pin_dir / "base-manifest.json").read_text(encoding="utf-8"))
    if manifest["config"]["digest"] != "sha256:" + pin["base_config_sha256"]:
        raise ValueError("Pinned base configuration identity is inconsistent")
    if shutil.disk_usage(output).free < 3 * 1024**3:
        raise ValueError("Replay setup requires at least 3 GiB of free space")
    base_client = DockerClient(root, output / "base-client", runtime)
    captures = []
    for name in ("crane", "node"):
        captures.append({"asset": name, **download(pin[name], output / (name + ".tar.gz"))})
        write_json(output / "downloads.json", captures)
    crane = admit_crane(output / "crane.tar.gz", pin["crane"], output / "crane")
    layer = node_layer(output / "node.tar.gz", pin["node"], output / "node-layer.tar")
    write_json(output / "node-layer.json", layer)
    home, temporary = output / "home", output / "temporary"
    home.mkdir()
    temporary.mkdir()
    environment = dict(base_client.environment)
    environment.update(
        HOME=str(home),
        USERPROFILE=str(home),
        TEMP=str(temporary),
        TMP=str(temporary),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_RUNTIME_DIR=str(home / ".runtime"),
        REGISTRY_AUTH_FILE=str(home / "absent-auth.json"),
        GOMEMLIMIT="384MiB",
        GOMAXPROCS="2",
    )
    specification = file_sha256(pin_dir / "pins.json")
    tag = "ai-skills-node-replay:spec-" + specification[:16]
    label = "org.ai-skills-benchmarked.replay-spec"
    packet = output / "image.tar"
    native_phase(
        output,
        [
            str(crane),
            "mutate",
            pin["base_image_reference"],
            "--append",
            str(output / "node-layer.tar"),
            "--env",
            "PATH=" + PATH_VALUE,
            "--label",
            label + "=" + specification,
            "--output",
            str(packet),
            "--tag",
            tag,
            "--platform",
            "linux/amd64",
        ],
        environment,
    )
    item = remove_owned_tag(packet, tag)
    with tarfile.open(packet, "r:") as archive:
        source = archive.extractfile(item["Config"])
        if source is None:
            raise ValueError("Missing assembled image configuration")
        with source:
            config_bytes = source.read()
            config = strict_json(config_bytes.decode("utf-8"))
    expected = copy.deepcopy(base)
    expected["config"]["Env"][0] = "PATH=" + PATH_VALUE
    expected["config"].setdefault("Labels", {})[label] = specification
    expected["rootfs"]["diff_ids"].append("sha256:" + pin["node"]["layer_sha256"])
    expected["history"].append({"created": "0001-01-01T00:00:00Z"})
    layers = [row["digest"].removeprefix("sha256:") + ".tar.gz" for row in manifest["layers"]]
    layers.append(pin["node"]["compressed_layer_sha256"] + ".tar.gz")
    if config != expected or item["Layers"] != layers:
        raise ValueError("Replay changed more than its declared layer, PATH and provenance label")
    image_id = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
    archive_hash = file_sha256(packet)
    validate_image_archive(packet, archive_hash, image_id)
    generated = {key: value for key, value in supplied.items() if key != "image_manifest"}
    generated.update(
        schema_version=2, image_reference=image_id, image_archive=str(packet), image_archive_sha256=archive_hash
    )
    write_json(output / "runtime.json", generated)
    client = DockerClient(root, output / "replay-client", output / "runtime.json")
    probes = runtime_probes(client, output, pin["node"])
    if implementation(root) != sources:
        raise ValueError("Replay setup implementation changed during execution")
    artifacts = {
        path.relative_to(output).as_posix(): {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
        for path in sorted(output.rglob("*"))
        if path.is_file()
    }
    result = {
        "schema_version": 1,
        "passed": True,
        "source_sha256": sources,
        "artifacts": artifacts,
        "image_id": image_id,
        "runtime": "runtime.json",
        "probes": probes,
        "specification_sha256": specification,
        "publisher_equivalent": False,
        "task_execution_admitted": False,
        "model_invocations": 0,
        "counted_attempts": 0,
        "persistent_build_service_created": False,
        "registry_writes": False,
    }
    write_json(output / "result.json", result)
    return result


def check(root: Path, output: Path) -> dict[str, Any]:
    ordinary(output)
    if not output.resolve().is_relative_to(root / ".venv"):
        raise ValueError("Replay receipt must stay inside this checkout's .venv")
    result = strict_json((output / "result.json").read_text(encoding="utf-8"))
    if result["passed"] is not True or result["source_sha256"] != implementation(root):
        raise ValueError("Replay receipt is incomplete or its implementation changed")
    observed = {}
    for path in sorted(output.rglob("*")):
        ordinary(path)
        if path.is_file() and path != output / "result.json":
            observed[path.relative_to(output).as_posix()] = {"bytes": path.stat().st_size, "sha256": file_sha256(path)}
    if observed != result["artifacts"]:
        raise ValueError("Replay artifacts changed or unexpected files appeared")
    runtime = strict_json((output / "runtime.json").read_text(encoding="utf-8"))
    if (
        runtime["image_reference"] != result["image_id"]
        or Path(runtime["image_archive"]).resolve() != output.resolve() / "image.tar"
    ):
        raise ValueError("Generated runtime points at a different image")
    validate_image_archive(output / "image.tar", runtime["image_archive_sha256"], result["image_id"])
    return {
        "passed": True,
        "scope": "offline artifact integrity only; engine and runtime probes are not repeated",
        "image_id": result["image_id"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, help="Qualified publisher-base runtime declaration; required for setup")
    parser.add_argument(
        "--output", type=Path, required=True, help="Unused owned .venv directory, or existing receipt for --check"
    )
    parser.add_argument(
        "--check", action="store_true", help="Verify existing artifacts without network or engine access"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.check and args.runtime is None:
        parser.error("--runtime is required for setup")
    try:
        result = (
            check(ROOT, args.output.resolve()) if args.check else prepare(ROOT, args.runtime.resolve(), args.output)
        )
        print(json.dumps({key: value for key, value in result.items() if key not in {"source_sha256", "artifacts"}}))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, tarfile.TarError) as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__, "errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
