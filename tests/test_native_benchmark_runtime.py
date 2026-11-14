from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import _native_benchmark_runtime as runtime
import pytest


def _runtime(tmp_path: Path) -> tuple[Path, str]:
    cli = tmp_path / "docker.exe"
    cli.write_bytes(b"admitted native executable")
    image_id = "sha256:" + "1" * 64
    image = {
        "schemaVersion": 2,
        "config": {"digest": image_id},
        "layers": [{"size": 123}],
    }
    manifest = tmp_path / "manifest.json"
    raw = json.dumps(image).encode()
    manifest.write_bytes(raw)
    spec = {
        "schema_version": 1,
        "docker_cli": str(cli),
        "docker_cli_sha256": hashlib.sha256(cli.read_bytes()).hexdigest(),
        "endpoint": "npipe:////./pipe/qualified-engine",
        "engine_id": "expected-engine",
        "image_reference": "docker.io/publisher/image@sha256:" + hashlib.sha256(raw).hexdigest(),
        "image_manifest": str(manifest),
    }
    path = tmp_path / "runtime.json"
    path.write_text(json.dumps(spec))
    return path, image_id


def test_runtime_rejects_cli_change_before_engine_use(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec, _ = _runtime(tmp_path)
    (tmp_path / "docker.exe").write_bytes(b"changed")
    (tmp_path / ".venv").mkdir()
    calls = []
    monkeypatch.setattr(runtime.DockerClient, "run", lambda *args, **kwargs: calls.append(args))
    with pytest.raises(ValueError, match="Docker executable"):
        runtime.DockerClient(tmp_path, tmp_path / ".venv/output", spec)
    assert calls == []


@pytest.mark.parametrize("changed", ["engine", "image", "manifest"])
def test_runtime_binds_engine_and_image_before_container_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: str
) -> None:
    spec, image_id = _runtime(tmp_path)
    (tmp_path / ".venv").mkdir()
    calls = []

    def inspect(self: Any, label: str, args: list[str], **kwargs: Any) -> bytes:
        calls.append(args)
        if args[0] == "info":
            return json.dumps(
                {
                    "ID": "different" if changed == "engine" else "expected-engine",
                    "OSType": "linux",
                    "Architecture": "x86_64",
                }
            ).encode()
        assert args[:2] == ["image", "inspect"]
        return json.dumps(
            [
                {
                    "Id": "sha256:" + "2" * 64 if changed == "image" else image_id,
                    "Os": "linux",
                    "Architecture": "amd64",
                }
            ]
        ).encode()

    monkeypatch.setattr(runtime.DockerClient, "run", inspect)
    if changed == "manifest":
        (tmp_path / "manifest.json").write_bytes(b"changed")
    with pytest.raises(ValueError):
        runtime.DockerClient(tmp_path, tmp_path / ".venv/output", spec)
    assert all(args[0] != "container" for args in calls)


def test_repository_workspace_stays_within_declared_tmpfs_boundary() -> None:
    resources = runtime.LeaseResources(repository_workspace=True)
    assert resources.mounts()["/workspace"] == "rw,nosuid,nodev,noexec,size=16777216,mode=0755"
    with pytest.raises(ValueError, match="Repository workspace"):
        runtime.LeaseResources(repository_workspace=1)  # type: ignore[arg-type]


def test_full_project_profile_declares_cpu_storage_and_execution_separately() -> None:
    resources = runtime.LeaseResources(
        memory_bytes=8 * 1024**3,
        tmpfs_bytes=1024**3,
        repository_workspace=True,
        repository_bytes=4 * 1024**3,
        repository_executable=True,
        cpu_count=4,
    )
    assert resources.mounts() == {
        "/tmp": "rw,nosuid,nodev,noexec,size=1073741824,mode=1777",
        "/workspace": "rw,nosuid,nodev,exec,size=4294967296,mode=0755",
    }
    assert runtime.LeaseResources(**asdict(resources)) == resources


@pytest.mark.parametrize(
    "options",
    [
        {"cpu_count": True},
        {"cpu_count": 1.0},
        {"cpu_count": 0},
        {"cpu_count": 5},
        {"memory_bytes": 8 * 1024**3 + 1},
        {"repository_bytes": True},
        {"repository_workspace": True, "repository_bytes": 6 * 1024**3 + 1},
        {"repository_workspace": True, "repository_bytes": 16 * 1024**2 - 1},
        {"repository_workspace": True, "repository_executable": 1},
        {"repository_executable": True},
        {"repository_bytes": 32 * 1024**2},
        {"tmpfs_bytes": 192 * 1024**2, "repository_workspace": True},
        {"tmpfs_bytes": 176 * 1024**2, "task_workspace": True},
    ],
)
def test_resource_profiles_reject_invalid_or_unfunded_combined_mounts(options: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        runtime.LeaseResources(**options)


def test_combined_mount_budget_accounts_for_all_four_task_mounts() -> None:
    resources = runtime.LeaseResources(tmpfs_bytes=168 * 1024**2, task_workspace=True)
    assert len(resources.mounts()) == 5


@pytest.mark.parametrize("seconds", [900, 1200, 1800, 2460, 3600])
def test_lease_preserves_long_publisher_deadlines_and_legacy_journal_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, seconds: int
) -> None:
    (tmp_path / ".venv").mkdir()
    owners = SimpleNamespace(claim=lambda: runtime.ProcessIdentity(123, 456), alive=lambda owner: False)
    monkeypatch.setattr(runtime, "process_owners", lambda: owners)
    client: Any = SimpleNamespace(root=tmp_path, root_id="a" * 64, image_id="sha256:" + "b" * 64, ids=lambda token: [])
    path = tmp_path / ".venv/lease.json"
    lease = runtime.ContainerLease(client, path, seconds=seconds)
    assert lease.record["lease_seconds"] == seconds
    old = json.loads(path.read_bytes())
    for name in ("cpu_count", "repository_bytes", "repository_executable"):
        del old["resources"][name]
    original = json.dumps(old).encode()
    path.write_bytes(original)
    recovered = runtime.ContainerLease.recover(client, path)
    assert recovered.seconds == seconds and recovered.resources == runtime.LeaseResources()
    assert path.read_bytes() == original


@pytest.mark.parametrize("seconds", [True, False, 1.0, 0, 3601])
def test_invalid_lease_deadline_is_rejected_before_owner_or_engine_use(tmp_path: Path, seconds: Any) -> None:
    client: Any = SimpleNamespace(root=tmp_path)
    with pytest.raises(ValueError, match="duration"):
        runtime.ContainerLease(client, tmp_path / ".venv/lease.json", seconds=seconds)


def test_missing_native_image_pulls_the_frozen_digest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec, image_id = _runtime(tmp_path)
    declared = json.loads(spec.read_bytes())
    (tmp_path / ".venv").mkdir()
    calls = []
    inspected = 0

    def native(self: Any, label: str, args: list[str], **kwargs: Any) -> bytes:
        nonlocal inspected
        config_path = Path(self.environment["DOCKER_CONFIG"]) / "config.json"
        assert config_path == self.config / "config.json"
        config = json.loads(config_path.read_bytes())
        assert config["credsStore"] == "" and config["credHelpers"] == {}
        # A nonempty map suppresses the CLI's platform-store autodetection.
        assert set(config["auths"]) == {"https://index.docker.io/v1/"}
        assert all(value == {} for value in config["auths"].values())
        calls.append(args)
        if args[0] == "info":
            return json.dumps({"ID": "expected-engine", "OSType": "linux", "Architecture": "x86_64"}).encode()
        if args[:2] == ["image", "pull"]:
            return b""
        assert args[:2] == ["image", "inspect"]
        inspected += 1
        if inspected == 1:
            return b""
        return json.dumps([{"Id": image_id, "Os": "linux", "Architecture": "amd64"}]).encode()

    monkeypatch.setattr(runtime.DockerClient, "run", native)
    client = runtime.DockerClient(tmp_path, tmp_path / ".venv/output", spec)
    assert client.image_id == image_id
    assert ["image", "pull", "--platform=linux/amd64", declared["image_reference"]] in calls
    assert inspected == 2


@pytest.mark.parametrize("present", [False, True])
def test_local_replay_loads_only_a_verified_archive_without_registry_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, present: bool
) -> None:
    from test_native_image_archive import archive_fixture

    spec, _ = _runtime(tmp_path)
    owned = tmp_path / ".venv"
    owned.mkdir()
    packet = owned / "image.tar"
    digest, image_id = archive_fixture(packet)
    declared = json.loads(spec.read_bytes())
    declared.pop("image_manifest")
    declared.update(schema_version=2, image_reference=image_id, image_archive=str(packet), image_archive_sha256=digest)
    spec.write_text(json.dumps(declared))
    if present:
        packet.unlink()  # The exact content ID is sufficient when already installed.
    loaded = False
    calls: list[list[str]] = []

    def native(self: Any, label: str, args: list[str], **kwargs: Any) -> bytes:
        nonlocal loaded
        calls.append(args)
        if args[0] == "info":
            return json.dumps({"ID": "expected-engine", "OSType": "linux", "Architecture": "amd64"}).encode()
        if args[:2] == ["image", "load"]:
            assert args == ["image", "load", "--input", str(packet)]
            loaded = True
            return b""
        assert args == ["image", "inspect", image_id]
        return json.dumps(
            [{"Id": image_id, "Os": "linux", "Architecture": "amd64"}] if loaded or present else []
        ).encode()

    monkeypatch.setattr(runtime.DockerClient, "run", native)
    assert runtime.DockerClient(tmp_path, owned / "output", spec).image_id == image_id
    assert loaded is not present
    assert not any(args[:2] == ["image", "pull"] for args in calls)


@pytest.mark.parametrize("pid,birth", [(True, 1), (1, False), (0, 1), (1, 0)])
def test_owner_identity_rejects_invalid_process_incarnations(pid: Any, birth: Any) -> None:
    with pytest.raises(ValueError):
        runtime.ProcessIdentity(pid, birth)
