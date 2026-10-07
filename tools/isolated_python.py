"""Execute explicitly staged Python files in a bounded, inspected Docker container.

Returned candidate data is untrusted. The caller must score it outside the
container against independently defined expectations. This is not an agent
runner, a benchmark score, or a container escape certification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

IMAGE = "python@sha256:89fb7d3da20043c370643435258bdd7ab755d326d359001d02988ed15ae5219e"
WORKER = Path(__file__).with_name("_isolated_worker.py")
OWNER_LABEL = "ai-skills.isolated-invocation"
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_STAGED_BYTES = 32 * 1024 * 1024
MAX_REQUEST_BYTES = 16 * 1024 * 1024
PROFILES = {
    "python-small": {"cpus": 1, "memory_mib": 512, "pids": 64},
    "skillsbench-tfidf": {"cpus": 8, "memory_mib": 4096, "pids": 256},
}


def relative_file(name: str) -> str:
    path = PurePosixPath(name)
    if not name or "\\" in name or ":" in name or path.is_absolute() or path.as_posix() != name:
        raise ValueError("file must use a canonical relative POSIX path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe relative file")
    return name


def stage_files(source: Path, names: list[str], destination: Path) -> dict[str, str]:
    """Copy explicit regular files only, rejecting links and oversized inputs."""
    if not names or len(names) != len({name.casefold() for name in names}):
        raise ValueError("file selection must be nonempty and unique")
    source = source.absolute()
    hashes = {}
    total = 0
    for name in names:
        relative_file(name)
        path = source / name
        for parent in (path, *path.parents):
            info = parent.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ValueError("staged path or parent is a link/reparse point")
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError("staged input must be a contained regular file")
        if info.st_size > MAX_FILE_BYTES:
            raise ValueError("staged file exceeds size bound")
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
        total += len(data)
        if len(data) > MAX_FILE_BYTES or total > MAX_STAGED_BYTES:
            raise ValueError("staged inputs exceed size bound")
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        hashes[name] = hashlib.sha256(data).hexdigest()
    return hashes


def docker_call(arguments: list[str], *, timeout: float = 15) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["docker", *arguments], capture_output=True, timeout=timeout, check=False)


def validate_inspection(
    record: dict[str, Any], token: str, profile: str = "python-small", *, image: str = IMAGE
) -> list[str]:
    """Fail closed on isolation constraints before starting candidate code."""
    errors = []
    resources = PROFILES[profile]
    config = record.get("Config", {})
    host = record.get("HostConfig", {})
    expected = {
        "NetworkMode": "none",
        "IpcMode": "none",
        "ReadonlyRootfs": True,
        "Memory": resources["memory_mib"] * 1024 * 1024,
        "MemorySwap": resources["memory_mib"] * 1024 * 1024,
        "NanoCpus": resources["cpus"] * 1_000_000_000,
        "PidsLimit": resources["pids"],
        "Privileged": False,
        "Init": True,
    }
    for key, value in expected.items():
        if host.get(key) != value:
            errors.append(f"unexpected {key}")
    if config.get("User") != "65534:65534" or config.get("Image") != image:
        errors.append("unexpected user or image")
    if image.startswith("sha256:") and record.get("Image") != image:
        errors.append("resolved local image ID mismatch")
    if config.get("Labels", {}).get(OWNER_LABEL) != token:
        errors.append("ownership mismatch")
    if set(host.get("CapDrop") or []) != {"ALL"} or host.get("CapAdd"):
        errors.append("unexpected capabilities")
    if not any(item in {"no-new-privileges", "no-new-privileges:true"} for item in host.get("SecurityOpt") or []):
        errors.append("no-new-privileges missing")
    if host.get("LogConfig", {}).get("Type") != "none":
        errors.append("container log storage enabled")
    mounts = record.get("Mounts", [])
    if len(mounts) != 2 or {item.get("Destination") for item in mounts} != {"/submission", "/worker"}:
        errors.append("unexpected mount set")
    if any(item.get("RW") is not False or item.get("Type") != "bind" for item in mounts):
        errors.append("unexpected writable or non-bind mount")
    temporary = host.get("Tmpfs", {})
    if set(temporary) != {"/tmp"} or not {"noexec", "nosuid", "size=128m"}.issubset(
        set(temporary.get("/tmp", "").split(","))
    ):
        errors.append("unexpected temporary filesystem")
    if host.get("Devices") or host.get("DeviceRequests") or host.get("VolumesFrom"):
        errors.append("extra host devices or volumes")
    return errors


def parse_response(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate response key")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise ValueError(f"nonfinite response number: {value}")

    result = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    if (
        not isinstance(result, dict)
        or not isinstance(result.get("worker_status"), str)
        or result["worker_status"] not in {"returned", "error"}
    ):
        raise ValueError("invalid worker response envelope")
    if result["worker_status"] == "returned" and set(result) != {"worker_status", "result"}:
        raise ValueError("returned response must contain exactly status and result")
    return result


def run_isolated(
    source: Path,
    names: list[str],
    request: Any,
    *,
    entrypoint: str = "candidate.py",
    timeout: float = 10,
    output_limit: int = 256 * 1024,
    profile: str = "python-small",
    image: str = IMAGE,
) -> dict[str, Any]:
    """Run one candidate request and remove only its verified owned container."""
    relative_file(entrypoint)
    if image != IMAGE and not re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        raise ValueError("dependency image must be an immutable local image ID")
    if profile not in PROFILES:
        raise ValueError("unknown resource profile")
    resources = PROFILES[profile]
    if entrypoint not in names:
        raise ValueError("entrypoint must be explicitly staged")
    if not math.isfinite(timeout) or not 0 < timeout <= 600:
        raise ValueError("timeout must be finite and within 600 seconds")
    if isinstance(output_limit, bool) or not 1024 <= output_limit <= 16 * 1024 * 1024:
        raise ValueError("output bound must be between 1 KiB and 16 MiB")
    payload = json.dumps(request, allow_nan=False).encode("utf-8")
    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("request exceeds size bound")
    token = uuid.uuid4().hex
    name = "skills-invoke-" + token
    worker_bytes = WORKER.read_bytes()
    report: dict[str, Any] = {
        "status": "infrastructure_error",
        "container_name": name,
        "image": image,
        "scored": False,
        "candidate_response_is_untrusted": True,
        "cleanup_verified": False,
        "request_sha256": hashlib.sha256(payload).hexdigest(),
        "worker_sha256": hashlib.sha256(worker_bytes).hexdigest(),
        "resource_profile": profile,
    }
    setup_start = time.monotonic()
    process: subprocess.Popen[bytes] | None = None
    threads: list[threading.Thread] = []
    container_id: str | None = None
    with tempfile.TemporaryDirectory(prefix="skills-invoke-") as temporary:
        base = Path(temporary)
        submission = base / "submission"
        worker = base / "worker"
        submission.mkdir()
        worker.mkdir()
        report["submission_sha256"] = stage_files(source, names, submission)
        (worker / "invoke.py").write_bytes(worker_bytes)
        if any("," in str(path) for path in (submission, worker)):
            raise ValueError("mount path contains a Docker delimiter")
        try:
            created = docker_call(
                [
                    "create",
                    "--pull",
                    "never",
                    "--name",
                    name,
                    "--label",
                    OWNER_LABEL + "=" + token,
                    "--interactive",
                    "--network",
                    "none",
                    "--ipc",
                    "none",
                    "--read-only",
                    "--user",
                    "65534:65534",
                    "--cap-drop",
                    "ALL",
                    "--security-opt",
                    "no-new-privileges",
                    "--cpus",
                    str(resources["cpus"]),
                    "--memory",
                    f"{resources['memory_mib']}m",
                    "--memory-swap",
                    f"{resources['memory_mib']}m",
                    "--pids-limit",
                    str(resources["pids"]),
                    "--tmpfs",
                    "/tmp:rw,noexec,nosuid,size=128m",
                    "--init",
                    "--log-driver",
                    "none",
                    "--mount",
                    f"type=bind,source={submission},target=/submission,readonly",
                    "--mount",
                    f"type=bind,source={worker},target=/worker,readonly",
                    "--workdir",
                    "/submission",
                    image,
                    "python",
                    "-I",
                    "-B",
                    "/worker/invoke.py",
                    "--entrypoint",
                    entrypoint,
                    "--request-limit",
                    str(MAX_REQUEST_BYTES),
                    "--output-limit",
                    str(output_limit),
                ]
            )
            if created.returncode:
                raise RuntimeError("Docker create failed: " + created.stderr.decode("utf-8", errors="replace")[:2048])
            container_id = created.stdout.decode("ascii").strip()
            if not re.fullmatch(r"[0-9a-f]{64}", container_id):
                raise RuntimeError("Docker returned an invalid container ID")
            report["container_id"] = container_id
            inspected = docker_call(["inspect", container_id])
            if inspected.returncode:
                raise RuntimeError("created container inspection failed")
            inspection = json.loads(inspected.stdout)[0]
            errors = validate_inspection(inspection, token, profile, image=image)
            report["isolation_checks"] = {
                "errors": errors,
                "passed": not errors,
                "observed_user": inspection["Config"].get("User"),
                "observed_image": inspection["Config"].get("Image"),
                "observed_ownership_token": inspection["Config"].get("Labels", {}).get(OWNER_LABEL),
                "resolved_image_id": inspection.get("Image"),
                "observed_host_constraints": {
                    key: inspection["HostConfig"].get(key)
                    for key in (
                        "NetworkMode",
                        "IpcMode",
                        "ReadonlyRootfs",
                        "Memory",
                        "MemorySwap",
                        "NanoCpus",
                        "PidsLimit",
                        "Privileged",
                        "Init",
                        "CapDrop",
                        "CapAdd",
                        "SecurityOpt",
                        "LogConfig",
                        "Tmpfs",
                        "Devices",
                        "DeviceRequests",
                        "VolumesFrom",
                    )
                },
                "observed_mounts": [
                    {key: mount.get(key) for key in ("Destination", "Type", "RW")}
                    for mount in inspection.get("Mounts", [])
                ],
            }
            if errors:
                raise RuntimeError("container constraints failed inspection: " + ", ".join(errors))
            report["setup_elapsed_seconds"] = time.monotonic() - setup_start
            process = subprocess.Popen(
                ["docker", "start", "--attach", "--interactive", container_id],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            buffers = {"stdout": bytearray(), "stderr": bytearray()}
            lock = threading.Lock()
            overflow = threading.Event()
            output_bytes = 0

            def read_stream(stream: Any, key: str) -> None:
                nonlocal output_bytes
                try:
                    while chunk := stream.read(4096):
                        with lock:
                            remaining = max(0, output_limit - output_bytes)
                            buffers[key].extend(chunk[:remaining])
                            output_bytes += len(chunk)
                            if output_bytes > output_limit:
                                overflow.set()
                finally:
                    stream.close()

            def write_input(stream: Any) -> None:
                try:
                    stream.write(payload)
                    stream.flush()
                except (BrokenPipeError, OSError):
                    pass
                finally:
                    stream.close()

            for stream, key in ((process.stdout, "stdout"), (process.stderr, "stderr")):
                thread = threading.Thread(target=read_stream, args=(stream, key), daemon=True)
                threads.append(thread)
                thread.start()
            writer = threading.Thread(target=write_input, args=(process.stdin,), daemon=True)
            threads.append(writer)
            writer.start()
            runtime_start = time.monotonic()
            while process.poll() is None and not overflow.is_set():
                if time.monotonic() - runtime_start >= timeout:
                    report["status"] = "timeout"
                    break
                overflow.wait(min(0.05, max(0, timeout - (time.monotonic() - runtime_start))))
            report["runtime_elapsed_seconds"] = time.monotonic() - runtime_start
            if overflow.is_set():
                report["status"] = "output_limit"
            elif report["status"] != "timeout":
                for thread in threads:
                    thread.join(timeout=2)
                report["returncode"] = process.returncode
                try:
                    if overflow.is_set():
                        report["status"] = "output_limit"
                    else:
                        response = parse_response(bytes(buffers["stdout"]))
                        report["candidate_response"] = response
                        report["status"] = "completed" if response["worker_status"] == "returned" else "worker_error"
                        if process.returncode:
                            report["status"] = "execution_error"
                except (UnicodeError, ValueError, RecursionError) as exc:
                    report["status"] = "invalid_response"
                    report["detail"] = str(exc)[:2048]
            report["captured_bytes"] = sum(len(value) for value in buffers.values())
            report["stderr"] = bytes(buffers["stderr"]).decode("utf-8", errors="replace")
        except (OSError, ValueError, subprocess.TimeoutExpired, RuntimeError) as exc:
            report["detail"] = str(exc)[:2048]
        finally:
            try:
                owned = docker_call(["inspect", name])
                if owned.returncode == 0:
                    info = json.loads(owned.stdout)[0]
                    actual_id = info["Id"]
                    if info.get("Config", {}).get("Labels", {}).get(OWNER_LABEL) != token:
                        raise RuntimeError("cleanup ownership mismatch")
                    if container_id is not None and actual_id != container_id:
                        raise RuntimeError("cleanup container ID mismatch")
                    removed = docker_call(["rm", "--force", actual_id])
                    if removed.returncode:
                        raise RuntimeError("owned container removal failed")
                check = docker_call(["ps", "--all", "--quiet", "--filter", "label=" + OWNER_LABEL + "=" + token])
                if check.returncode or check.stdout.strip():
                    raise RuntimeError("container cleanup not verified")
                report["cleanup_verified"] = True
            except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as exc:
                report["cleanup_error"] = str(exc)[:2048]
            if process is not None:
                if process.poll() is None:
                    process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    report["cleanup_error"] = "Docker client did not terminate"
                    report["cleanup_verified"] = False
            for thread in threads:
                thread.join(timeout=2)
            if any(thread.is_alive() for thread in threads):
                report["cleanup_error"] = "Docker transport thread did not terminate"
                report["cleanup_verified"] = False
    report["elapsed_seconds"] = time.monotonic() - setup_start
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--file", action="append", required=True, dest="files")
    parser.add_argument("--entrypoint", default="candidate.py")
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--output-limit", type=int, default=256 * 1024)
    parser.add_argument("--profile", choices=sorted(PROFILES), default="python-small")
    parser.add_argument("--image", default=IMAGE, help="Qualified base or immutable local dependency image ID")
    parser.add_argument("--json", action="store_true", help="Emit the untrusted execution result as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.request.stat().st_size > MAX_REQUEST_BYTES:
            raise ValueError("request file exceeds size bound")
        with args.request.open("rb") as stream:
            raw = stream.read(MAX_REQUEST_BYTES + 1)
        if len(raw) > MAX_REQUEST_BYTES:
            raise ValueError("request file exceeds size bound")
        request = json.loads(raw.decode("utf-8"))
        report = run_isolated(
            args.submission,
            args.files,
            request,
            entrypoint=args.entrypoint,
            timeout=args.timeout,
            output_limit=args.output_limit,
            profile=args.profile,
            image=args.image,
        )
    except (OSError, ValueError, RecursionError) as exc:
        report = {"status": "invalid_input", "detail": str(exc)}
    print(json.dumps(report, indent=2) if args.json else str(report["status"]))
    return 0 if report["status"] == "completed" and report.get("cleanup_verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
