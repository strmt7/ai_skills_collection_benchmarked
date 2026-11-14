"""Owned native benchmark containers with bounded leases and explicit runtime pins."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import sys
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from _native_image_archive import validate_image_archive
from _trial_transcript import strict_json
from _windows_trial_process import run_owned


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    temporary = path.with_name(path.name + ".writing")
    with temporary.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def anonymous_registry_config() -> dict[str, object]:
    """Disable Docker's default credential-store discovery for public image reads.

    An empty auth map allows the CLI to discover a platform credential helper.
    One explicit empty Docker Hub entry prevents that discovery without adding
    credentials. Keep both helper settings empty in the private configuration.
    """
    return {"auths": {"https://index.docker.io/v1/": {}}, "credsStore": "", "credHelpers": {}}


@dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    creation_filetime: int

    def __post_init__(self) -> None:
        if isinstance(self.pid, bool) or not isinstance(self.pid, int) or not 0 < self.pid < 2**32:
            raise ValueError("Invalid owner PID")
        if (
            isinstance(self.creation_filetime, bool)
            or not isinstance(self.creation_filetime, int)
            or not 0 < self.creation_filetime < 2**64
        ):
            raise ValueError("Invalid owner creation time")


class ProcessOwnerReader(Protocol):
    def claim(self) -> ProcessIdentity: ...
    def alive(self, identity: ProcessIdentity) -> bool: ...


if sys.platform == "win32":

    class _WindowsOwners:
        """Check process incarnation through kernel handles, not a name or PID alone."""

        def __init__(self) -> None:
            from ctypes import wintypes as w

            self.w = w
            self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            self.kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
            self.kernel.OpenProcess.restype = w.HANDLE
            self.kernel.GetProcessTimes.argtypes = [w.HANDLE, *([ctypes.POINTER(w.FILETIME)] * 4)]
            self.kernel.GetProcessTimes.restype = w.BOOL
            self.kernel.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
            self.kernel.WaitForSingleObject.restype = w.DWORD
            self.kernel.CloseHandle.argtypes = [w.HANDLE]
            self.kernel.CloseHandle.restype = w.BOOL

        def _close(self, handle: int) -> None:
            if not self.kernel.CloseHandle(handle):
                raise ctypes.WinError(ctypes.get_last_error())

        def _pid_present(self, pid: int) -> bool:
            w = self.w

            class ProcessEntry(ctypes.Structure):
                _fields_ = [
                    ("dwSize", w.DWORD),
                    ("cntUsage", w.DWORD),
                    ("pid", w.DWORD),
                    ("heap", ctypes.c_size_t),
                    ("module", w.DWORD),
                    ("threads", w.DWORD),
                    ("parent", w.DWORD),
                    ("priority", w.LONG),
                    ("flags", w.DWORD),
                    ("name", w.WCHAR * 260),
                ]

            self.kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
            self.kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
            for method in (self.kernel.Process32FirstW, self.kernel.Process32NextW):
                method.argtypes = [w.HANDLE, ctypes.POINTER(ProcessEntry)]
                method.restype = w.BOOL
            snapshot = self.kernel.CreateToolhelp32Snapshot(0x2, 0)
            if snapshot in (None, ctypes.c_void_p(-1).value):
                raise ctypes.WinError(ctypes.get_last_error())
            try:
                entry = ProcessEntry()
                entry.dwSize = ctypes.sizeof(entry)
                available = self.kernel.Process32FirstW(snapshot, ctypes.byref(entry))
                count = 0
                deadline = time.monotonic() + 5
                while available:
                    count += 1
                    if entry.pid == pid:
                        return True
                    if time.monotonic() > deadline:
                        raise TimeoutError("Process ownership snapshot did not complete")
                    entry.dwSize = ctypes.sizeof(entry)
                    available = self.kernel.Process32NextW(snapshot, ctypes.byref(entry))
                if ctypes.get_last_error() != 18 or not count:
                    raise RuntimeError("Process snapshot is incomplete or empty")
                return False
            finally:
                self._close(snapshot)

        def observe(self, pid: int) -> tuple[ProcessIdentity | None, bool]:
            if not isinstance(pid, int) or isinstance(pid, bool) or not 0 < pid < 2**32:
                raise ValueError("Invalid owner PID")
            handle = self.kernel.OpenProcess(0x1000 | 0x100000, False, pid)
            if not handle:
                error = ctypes.get_last_error()
                if self._pid_present(pid):
                    raise ctypes.WinError(error)
                return None, False
            try:
                times = [self.w.FILETIME() for _ in range(4)]
                if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
                    raise ctypes.WinError(ctypes.get_last_error())
                birth = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
                state = self.kernel.WaitForSingleObject(handle, 0)
                if state == 0xFFFFFFFF:
                    raise ctypes.WinError(ctypes.get_last_error())
                if state not in (0, 258):
                    raise RuntimeError("Unexpected process wait status")
                return ProcessIdentity(pid, birth), state == 258
            finally:
                self._close(handle)

        def claim(self) -> ProcessIdentity:
            identity, alive = self.observe(os.getpid())
            if identity is None or not alive:
                raise RuntimeError("Collector could not establish its own process identity")
            return identity

        def alive(self, identity: ProcessIdentity) -> bool:
            current, running = self.observe(identity.pid)
            return running and current == identity


def process_owners() -> ProcessOwnerReader:
    if sys.platform == "win32":
        return _WindowsOwners()
    raise RuntimeError("The native benchmark controller requires Windows")


class DockerError(RuntimeError):
    def __init__(self, label: str, stderr: bytes) -> None:
        super().__init__("Native Docker operation failed: " + label)
        self.stderr = stderr


class DockerClient:
    owner_label = "org.ai-skills-benchmarked.qualification"
    root_label = "org.ai-skills-benchmarked.source-root"

    def __init__(self, root: Path, output: Path, runtime: Path) -> None:
        self.root = root.resolve()
        self.output = output.resolve()
        if not self.output.is_relative_to(self.root / ".venv"):
            raise ValueError("Evidence must stay in this source root's owned ignored state")
        self.output.mkdir(exist_ok=False)
        (self.output / "runtime-implementation.py.txt").write_bytes(Path(__file__).read_bytes())
        self.root_id = sha256(str(self.root).casefold().encode())
        observed = strict_json(runtime.read_text(encoding="utf-8"))
        common = {
            "schema_version",
            "docker_cli",
            "docker_cli_sha256",
            "endpoint",
            "engine_id",
            "image_reference",
        }
        version = observed.get("schema_version") if isinstance(observed, dict) else None
        fields = common | ({"image_manifest"} if version == 1 else {"image_archive", "image_archive_sha256"})
        if (
            not isinstance(observed, dict)
            or set(observed) != fields
            or type(observed["schema_version"]) is not int
            or observed["schema_version"] not in (1, 2)
        ):
            raise ValueError("Native runtime must declare its CLI, engine and immutable image")
        self.docker = Path(observed["docker_cli"])
        if not self.docker.is_absolute() or sha256(self.docker.read_bytes()) != observed["docker_cli_sha256"]:
            raise ValueError("Docker executable differs from the runtime declaration")
        self.endpoint = observed["endpoint"]
        if not isinstance(self.endpoint, str) or not re.fullmatch(
            r"npipe:/{2,4}\./pipe/[A-Za-z0-9_.-]+", self.endpoint
        ):
            raise ValueError("Expected an explicit local Windows engine endpoint")
        self.reference = observed["image_reference"]
        archive_path = None
        if version == 1:
            if not isinstance(self.reference, str) or not re.fullmatch(
                r"docker.io/[a-z0-9._/-]+@sha256:[0-9a-f]{64}", self.reference
            ):
                raise ValueError("Expected an immutable public Docker image reference")
            manifest_path = Path(observed["image_manifest"])
            if not manifest_path.is_absolute() or manifest_path.stat().st_size > 1024**2:
                raise ValueError("Expected a bounded, explicit publisher manifest capture")
            raw_manifest = manifest_path.read_bytes()
            if "sha256:" + sha256(raw_manifest) != self.reference.split("@", 1)[1]:
                raise ValueError("Image manifest capture differs from the declared digest")
            manifest = strict_json(raw_manifest.decode("utf-8"))
            if manifest["schemaVersion"] != 2 or not isinstance(manifest["layers"], list):
                raise ValueError("Expected a platform-specific image manifest")
            if (
                any(type(layer.get("size")) is not int or layer["size"] < 0 for layer in manifest["layers"])
                or sum(layer["size"] for layer in manifest["layers"]) > 2 * 1024**3
            ):
                raise ValueError("Declared image exceeds the native benchmark image budget")
            self.image_id = manifest["config"]["digest"]
        else:
            self.image_id = self.reference
            archive_path = Path(observed["image_archive"])
            if (
                not archive_path.is_absolute()
                or not archive_path.resolve().is_relative_to(self.root / ".venv")
                or not isinstance(observed["image_archive_sha256"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", observed["image_archive_sha256"])
            ):
                raise ValueError("Expected a digest-bound archive in this checkout's ignored state")
        if not isinstance(self.image_id, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image_id):
            raise ValueError("Image configuration digest is malformed")
        self.config = self.output / "docker-config"
        self.config.mkdir()
        write_json(self.config / "config.json", anonymous_registry_config())
        self.environment = {
            key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "TEMP", "TMP") if key in os.environ
        }
        self.environment.update(
            PATH=os.pathsep.join((str(self.docker.parent), str(Path(os.environ["SYSTEMROOT"]) / "System32"))),
            DOCKER_CONFIG=str(self.config),
        )
        self.records: list[dict] = []
        self.counter = 0
        self._records_lock = threading.Lock()
        self.run_owned = run_owned
        engine = json.loads(self.run("engine", ["info", "--format", "{{json .}} "]))
        if (
            engine["ID"] != observed["engine_id"]
            or engine["OSType"] != "linux"
            or engine["Architecture"] not in {"x86_64", "amd64"}
        ):
            raise ValueError("Selected engine changed or is incompatible")
        image = json.loads(self.run("image", ["image", "inspect", self.reference], missing=True) or b"[]")
        if not image:
            if archive_path is None:
                self.run("pull-image", ["image", "pull", "--platform=linux/amd64", self.reference], timeout=240)
            else:
                validate_image_archive(archive_path, observed["image_archive_sha256"], self.image_id)
                self.run("load-image", ["image", "load", "--input", str(archive_path)], timeout=240)
            image = json.loads(self.run("pulled-image", ["image", "inspect", self.reference]))
        if (
            len(image) != 1
            or image[0]["Id"] != self.image_id
            or image[0]["Os"] != "linux"
            or image[0]["Architecture"] != "amd64"
        ):
            raise ValueError("Local image differs from the declared immutable identity")

    def run(self, label: str, arguments: list[str], *, timeout: float = 30, missing: bool = False) -> bytes:
        with self._records_lock:
            self.counter += 1
            label = f"{self.counter:03d}-" + label
        if not re.fullmatch(r"[a-z0-9-]+", label):
            raise ValueError("Invalid native command evidence label")
        argv = [str(self.docker), "--host", self.endpoint, "--config", str(self.config), *arguments]
        with (
            open(os.devnull, "rb") as stdin,
            (self.output / (label + ".stdout.native")).open("xb") as stdout,
            (self.output / (label + ".stderr.native")).open("xb") as stderr,
        ):
            result = self.run_owned(
                argv,
                cwd=self.root,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                output_limit=2 * 1024**2,
                memory_limit=512 * 1024**2,
                process_limit=16,
                environment=self.environment,
            )
        with self._records_lock:
            self.records.append({"argv": argv, "process": result})
            write_json(self.output / "processes.json", self.records)
        raw_error = (self.output / (label + ".stderr.native")).read_bytes()
        if (
            result["termination_reason"]
            or result["job_active_processes_after_cleanup"]
            or (result["exit_code"] != 0 and not (missing and result["exit_code"] == 1 and b"No such" in raw_error))
        ):
            raise DockerError(label, raw_error)
        return (self.output / (label + ".stdout.native")).read_bytes()

    def ids(self, token: str) -> list[str]:
        if not re.fullmatch(r"[0-9a-f]{32}", token):
            raise ValueError("Invalid qualification token")
        raw = self.run(
            "owned-identities",
            [
                "container",
                "ls",
                "--all",
                "--no-trunc",
                "--filter",
                "label=" + self.owner_label + "=" + token,
                "--format",
                "{{.ID}}",
            ],
        )
        identities = raw.decode("ascii").split()
        if any(not re.fullmatch(r"[0-9a-f]{64}", identity) for identity in identities):
            raise ValueError("Invalid native container ID")
        return identities

    def inspect(self, identity: str) -> dict | None:
        if not re.fullmatch(r"[0-9a-f]{64}", identity):
            raise ValueError("Expected an exact container ID")
        raw = self.run("inspect-container", ["container", "inspect", identity], missing=True)
        containers = json.loads(raw or b"[]")
        if not containers:
            rows = self.run(
                "confirm-absence",
                ["container", "ls", "--all", "--no-trunc", "--filter", "id=" + identity, "--format", "{{.ID}}"],
            )
            if rows.strip():
                raise RuntimeError("Container inspection failed while its ID remains present")
            return None
        if len(containers) != 1 or containers[0]["Id"] != identity:
            raise ValueError("Unexpected native container inspection")
        return containers[0]


@dataclass(frozen=True)
class LeaseResources:
    memory_bytes: int = 256 * 1024**2
    tmpfs_bytes: int = 16 * 1024**2
    pids_limit: int = 32
    executable_workspace: bool = False
    task_workspace: bool = False
    repository_workspace: bool = False
    cpu_count: int = 1
    repository_bytes: int = 16 * 1024**2
    repository_executable: bool = False

    def __post_init__(self) -> None:
        for value in (self.memory_bytes, self.tmpfs_bytes, self.pids_limit, self.cpu_count, self.repository_bytes):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Resource quantities require integers")
        if not 256 * 1024**2 <= self.memory_bytes <= 8 * 1024**3:
            raise ValueError("Memory request exceeds the declared experiment range")
        if not 16 * 1024**2 <= self.tmpfs_bytes <= 6 * 1024**3:
            raise ValueError("Workspace request leaves insufficient process memory")
        if not 32 <= self.pids_limit <= 128 or not isinstance(self.executable_workspace, bool):
            raise ValueError("Invalid process or workspace execution request")
        if not isinstance(self.task_workspace, bool):
            raise ValueError("Task workspace flag must be boolean")
        if not isinstance(self.repository_workspace, bool):
            raise ValueError("Repository workspace flag must be boolean")
        if not 1 <= self.cpu_count <= 4:
            raise ValueError("CPU request exceeds the declared experiment range")
        if not 16 * 1024**2 <= self.repository_bytes <= 6 * 1024**3:
            raise ValueError("Repository workspace size exceeds the declared experiment range")
        if not isinstance(self.repository_executable, bool):
            raise ValueError("Repository execution flag must be boolean")
        if not self.repository_workspace and (self.repository_executable or self.repository_bytes != 16 * 1024**2):
            raise ValueError("Repository options require a repository workspace")
        workspace_bytes = self.tmpfs_bytes + (self.repository_bytes if self.repository_workspace else 0)
        if self.task_workspace:
            workspace_bytes += 24 * 1024**2
        if workspace_bytes > 3 * self.memory_bytes // 4:
            raise ValueError("Combined workspaces leave insufficient process memory")

    def mounts(self) -> dict[str, str]:
        execution = "exec" if self.executable_workspace else "noexec"
        mounts = {"/tmp": f"rw,nosuid,nodev,{execution},size={self.tmpfs_bytes},mode=1777"}
        if self.task_workspace:
            mounts.update(
                {
                    "/app": "rw,nosuid,nodev,noexec,size=8388608,mode=1777",
                    "/logs": "rw,nosuid,nodev,noexec,size=8388608,mode=1777",
                    "/oracle": "rw,nosuid,nodev,noexec,size=4194304,mode=0755",
                    "/verifier": "rw,nosuid,nodev,noexec,size=4194304,mode=0755",
                }
            )
        if self.repository_workspace:
            repository_execution = "exec" if self.repository_executable else "noexec"
            mounts["/workspace"] = f"rw,nosuid,nodev,{repository_execution},size={self.repository_bytes},mode=0755"
        return mounts


class ContainerLease:
    def __init__(
        self,
        client: DockerClient,
        journal: Path,
        *,
        token: str | None = None,
        seconds: int = 25,
        resources: LeaseResources | None = None,
    ) -> None:
        self.client = client
        self.journal = journal.resolve()
        if not self.journal.is_relative_to(client.root / ".venv") or self.journal.exists():
            raise ValueError("An unused owned journal is required")
        if type(seconds) is not int or not 1 <= seconds <= 3600:
            raise ValueError("Lease duration is outside the experiment budget")
        self.token = token or uuid.uuid4().hex
        if not re.fullmatch(r"[0-9a-f]{32}", self.token):
            raise ValueError("Invalid lease token")
        self.name = "ai-skills-lease-" + self.token
        self.owner = process_owners().claim()
        self.seconds = seconds
        self.resources = resources or LeaseResources()
        self.identity: str | None = None
        self._heartbeat_stop = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self._heartbeat_error: str | None = None
        self.record = {
            "schema_version": 2,
            "source_root_sha256": client.root_id,
            "token": self.token,
            "name": self.name,
            "image_id": client.image_id,
            "owner": asdict(self.owner),
            "lease_seconds": seconds,
            "resources": asdict(self.resources),
            "stage": "planned",
            "container_id": None,
        }
        if client.ids(self.token):
            raise ValueError("Lease token already exists on the engine")
        write_json(self.journal, self.record)

    @classmethod
    def recover(cls, client: DockerClient, journal: Path) -> ContainerLease:
        if not journal.resolve().is_relative_to(client.root / ".venv"):
            raise ValueError("Recovery journal is outside owned state")
        record = json.loads(journal.read_bytes())
        if (
            record.get("schema_version") != 2
            or record["source_root_sha256"] != client.root_id
            or record["image_id"] != client.image_id
            or not re.fullmatch(r"[0-9a-f]{32}", record["token"])
            or record["name"] != "ai-skills-lease-" + record["token"]
        ):
            raise ValueError("Invalid or wrong-scope recovery journal")
        owner = ProcessIdentity(**record["owner"])
        if process_owners().alive(owner):
            raise RuntimeError("Recovery refuses a live matching creator incarnation")
        lease = object.__new__(cls)
        lease.client, lease.journal, lease.token, lease.name = client, journal, record["token"], record["name"]
        lease.owner, lease.seconds, lease.identity, lease.record = (
            owner,
            record["lease_seconds"],
            record["container_id"],
            record,
        )
        lease.resources = LeaseResources(**record["resources"])
        lease._heartbeat_stop = threading.Event()
        lease._heartbeat_thread = None
        lease._heartbeat_error = None
        return lease

    def _save(self, stage: str) -> None:
        self.record.update(stage=stage, container_id=self.identity)
        write_json(self.journal, self.record)

    def owned(self, identity: str) -> dict | None:
        container = self.client.inspect(identity)
        if container is None:
            return None
        labels = container["Config"].get("Labels") or {}
        if (
            container["Name"] != "/" + self.name
            or container["Image"] != self.client.image_id
            or labels.get(self.client.owner_label) != self.token
            or labels.get(self.client.root_label) != self.client.root_id
        ):
            raise ValueError("Container ownership mismatch; mutation refused")
        return container

    def create(self) -> str:
        if self.identity is not None or self.record["stage"] != "planned":
            raise RuntimeError("Lease has already created a container")
        program = (
            "import json,os,time;from pathlib import Path\n"
            "directory=Path('/tmp/lease-control');directory.mkdir(mode=0o700,exist_ok=True);heartbeat=directory/'heartbeat'\n"
            "started=time.monotonic();maximum=" + str(self.seconds) + ";grace=8\n"
            "if not heartbeat.exists():heartbeat.write_text(str(started));heartbeat.chmod(0o600)\n"
            "print(json.dumps({'pid':os.getpid(),'uid':os.getuid(),'lease_seconds':maximum,'heartbeat_grace_seconds':grace}),flush=True)\n"
            "while True:\n"
            " now=time.monotonic();last=float(heartbeat.read_text());age=now-last;elapsed=now-started\n"
            " reason='maximum_expired' if elapsed>=maximum else ('heartbeat_expired' if age>=grace or age<0 else None)\n"
            " if reason:print(json.dumps({'reason':reason,'elapsed_seconds':elapsed,'heartbeat_age_seconds':age}),flush=True);break\n"
            " time.sleep(0.1)"
        )
        mounts = self.resources.mounts()
        raw = self.client.run(
            "create-lease",
            [
                "container",
                "create",
                "--pull=never",
                "--platform=linux/amd64",
                "--name",
                self.name,
                "--label",
                self.client.owner_label + "=" + self.token,
                "--label",
                self.client.root_label + "=" + self.client.root_id,
                "--network=none",
                "--read-only",
                "--user=0:0",
                "--cpus=" + str(self.resources.cpu_count),
                "--memory=" + str(self.resources.memory_bytes),
                "--memory-swap=" + str(self.resources.memory_bytes),
                "--pids-limit=" + str(self.resources.pids_limit),
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--restart=no",
                "--init",
                "--stop-timeout=1",
                "--rm",
                "--log-driver=local",
                "--log-opt=max-size=1m",
                "--log-opt=max-file=1",
                "--log-opt=compress=false",
                *["--tmpfs=" + path + ":" + options for path, options in mounts.items()],
                "--entrypoint=python",
                self.client.reference,
                "-I",
                "-X",
                "utf8",
                "-B",
                "-c",
                program,
            ],
        )
        self.identity = raw.decode("ascii").strip()
        if not re.fullmatch(r"[0-9a-f]{64}", self.identity):
            raise ValueError("Creation returned no exact container ID")
        self._save("created")
        container = self.owned(self.identity)
        if container is None:
            raise RuntimeError("Created lease disappeared")
        host = container["HostConfig"]
        if (
            not host["AutoRemove"]
            or not host["ReadonlyRootfs"]
            or host["Privileged"]
            or host["NetworkMode"] != "none"
            or host["Memory"] != self.resources.memory_bytes
            or host["MemorySwap"] != self.resources.memory_bytes
            or host["NanoCpus"] != self.resources.cpu_count * 10**9
            or host["PidsLimit"] != self.resources.pids_limit
            or (host.get("Binds") or [])
            or host["Tmpfs"] != mounts
            or "ALL" not in host["CapDrop"]
            or not any(value.startswith("no-new-privileges") for value in host["SecurityOpt"])
        ):
            raise ValueError("Native lease configuration differs from the declared boundary")
        if (
            container["Config"]["User"] != "0:0"
            or not host["Init"]
            or host["LogConfig"]
            != {"Type": "local", "Config": {"max-size": "1m", "max-file": "1", "compress": "false"}}
        ):
            raise ValueError("Native watchdog or log bounds differ from the declared configuration")
        return self.identity

    def start(self) -> None:
        if self.identity is None or self.owned(self.identity) is None:
            raise RuntimeError("No owned container to start")
        self.client.run("start-lease", ["container", "start", self.identity])
        self._save("started")
        self._heartbeat_thread = threading.Thread(target=self._heartbeat, name="native-lease-" + self.token)
        self._heartbeat_thread.start()

    def _heartbeat(self) -> None:
        deadline = time.monotonic() + self.seconds
        program = (
            "import os,time;from pathlib import Path;directory=Path('/tmp/lease-control');directory.mkdir(mode=0o700,exist_ok=True);"
            "temporary=directory/'heartbeat.next';temporary.write_text(str(time.monotonic()));temporary.chmod(0o600);os.replace(temporary,directory/'heartbeat')"
        )
        try:
            identity = self.identity
            if identity is None:
                raise RuntimeError("No heartbeat target has been created")
            while not self._heartbeat_stop.is_set() and time.monotonic() < deadline:
                self.client.run(
                    "renew-lease",
                    ["container", "exec", "--user=0:0", identity, "python", "-I", "-X", "utf8", "-B", "-c", program],
                    timeout=4,
                )
                if self._heartbeat_stop.wait(2):
                    break
        except BaseException as error:
            self._heartbeat_error = repr(error)
            self._heartbeat_stop.set()

    def close(self) -> None:
        errors = []
        self._heartbeat_stop.set()
        if self._heartbeat_thread is not None:
            self._heartbeat_thread.join(10)
            if self._heartbeat_thread.is_alive():
                errors.append("Lease heartbeat thread did not stop")
        if self._heartbeat_error is not None:
            errors.append("Lease heartbeat failed: " + self._heartbeat_error)
        try:
            for identity in self.client.ids(self.token):
                container = self.owned(identity)
                if container is None:
                    continue
                if container["State"]["Running"]:
                    try:
                        self.client.run(
                            "stop-lease", ["container", "stop", "--timeout=1", identity], timeout=15, missing=True
                        )
                    except BaseException as error:
                        errors.append(repr(error))
                if self.owned(identity) is not None:
                    try:
                        self.client.run(
                            "remove-lease", ["container", "rm", "--force", identity], timeout=15, missing=True
                        )
                    except BaseException as error:
                        errors.append(repr(error))
            remaining = self.client.ids(self.token)
            if remaining:
                errors.append("Owned container IDs remain")
            if errors:
                raise RuntimeError("Lease cleanup failed: " + ";".join(errors))
            self._save("closed")
        except BaseException:
            write_json(
                self.journal.with_name(self.journal.name + ".cleanup-error.json"),
                {"errors": errors, "identity": self.identity},
            )
            raise


INPUT_RECEIVER = r"""
import hashlib,json,os,struct,sys
from pathlib import Path
size=struct.unpack(">I",sys.stdin.buffer.read(4))[0]
if not 0<size<=4096:raise ValueError("Invalid transfer header length")
head=json.loads(sys.stdin.buffer.read(size))
if set(head)!={"bytes","sha256"} or type(head["bytes"]) is not int or not 0<head["bytes"]<=64*1024**2:
    raise ValueError("Invalid native transfer header")
raw=sys.stdin.buffer.read(head["bytes"]+1)
if len(raw)!=head["bytes"] or hashlib.sha256(raw).hexdigest()!=head["sha256"]:
    raise ValueError("Native input digest mismatch")
target=Path("/tmp/benchmark-inputs.tar")
with target.open("xb") as output:output.write(raw)
target.chmod(0o444)
print(json.dumps({"bytes":len(raw),"sha256":head["sha256"],"uid":os.getuid()}))
"""

STAGE_INPUTS = r"""
import tarfile
from pathlib import Path,PurePosixPath
root=Path("/tmp/benchmark-inputs")
root.mkdir()
with tarfile.open("/tmp/benchmark-inputs.tar","r:") as archive:
    for entry in archive:
        name=PurePosixPath(entry.name)
        if not entry.isreg() or name.is_absolute() or ".." in name.parts or "\\" in entry.name:
            raise ValueError("Invalid staged input")
        target=root.joinpath(*name.parts)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as output:output.write(archive.extractfile(entry).read())
        target.chmod(0o444)
"""


def stage_inputs(lease: ContainerLease, output: Path, files: dict[str, bytes]) -> str:
    """Transfer one deterministic packet into an exact owned container."""
    import io
    import struct
    import tarfile

    from _trial_protocol import relative_path

    client = lease.client
    identity = lease.identity
    if identity is None or lease.owned(identity) is None:
        raise ValueError("Input staging requires an owned live container")
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, data in sorted(files.items()):
            relative_path(name)
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o444
            archive.addfile(member, io.BytesIO(data))
    raw = buffer.getvalue()
    if not 0 < len(raw) <= 64 * 1024**2:
        raise ValueError("Native task packet exceeds the qualified transfer budget")
    digest = sha256(raw)
    header = json.dumps({"bytes": len(raw), "sha256": digest}).encode()
    output.mkdir()
    packet = output / "packet.native"
    packet.write_bytes(struct.pack(">I", len(header)) + header + raw)
    argv = [
        str(client.docker),
        "--host",
        client.endpoint,
        "--config",
        str(client.config),
        "container",
        "exec",
        "--interactive",
        "--user=0:0",
        identity,
        "python",
        "-I",
        "-B",
        "-c",
        INPUT_RECEIVER,
    ]
    with (
        packet.open("rb") as stdin,
        (output / "stdout.native").open("xb") as stdout,
        (output / "stderr.native").open("xb") as stderr,
    ):
        process = client.run_owned(
            argv,
            cwd=client.root,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=30,
            output_limit=1024**2,
            memory_limit=512 * 1024**2,
            process_limit=16,
            environment=client.environment,
        )
    write_json(output / "process.json", {"argv": argv, "process": process})
    if process["exit_code"] or process["termination_reason"] or process["job_active_processes_after_cleanup"]:
        raise ValueError("Native input process did not complete")
    expected = {"bytes": len(raw), "sha256": digest, "uid": 0}
    if strict_json((output / "stdout.native").read_text(encoding="utf-8")) != expected:
        raise ValueError("Native input acknowledgement differs from the controller packet")
    client.run(
        "stage-inputs",
        ["container", "exec", "--user=0:0", identity, "python", "-I", "-B", "-c", STAGE_INPUTS],
    )
    return digest
