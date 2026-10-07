"""Isolation contract checks independent of any candidate skill wording."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import isolated_python as backend
import pytest
import qualify_isolated_python as qualification


def valid_inspection() -> dict[str, Any]:
    return {
        "Config": {"Image": backend.IMAGE, "User": "65534:65534", "Labels": {backend.OWNER_LABEL: "owned"}},
        "HostConfig": {
            "NetworkMode": "none",
            "IpcMode": "none",
            "ReadonlyRootfs": True,
            "Memory": 512 * 1024 * 1024,
            "MemorySwap": 512 * 1024 * 1024,
            "NanoCpus": 1_000_000_000,
            "PidsLimit": 64,
            "Privileged": False,
            "Init": True,
            "CapDrop": ["ALL"],
            "CapAdd": None,
            "SecurityOpt": ["no-new-privileges"],
            "LogConfig": {"Type": "none"},
            "Tmpfs": {"/tmp": "rw,noexec,nosuid,size=128m"},
        },
        "Mounts": [
            {"Destination": destination, "Type": "bind", "RW": False} for destination in ("/submission", "/worker")
        ],
    }


def test_inspection_accepts_qualified_contract() -> None:
    assert backend.validate_inspection(valid_inspection(), "owned") == []


def test_dependency_image_requires_exact_resolved_id_and_all_constraints() -> None:
    image = "sha256:" + "1" * 64
    record = valid_inspection()
    record["Config"]["Image"] = image
    record["Image"] = image
    assert backend.validate_inspection(record, "owned", image=image) == []
    record["Image"] = "sha256:" + "2" * 64
    assert backend.validate_inspection(record, "owned", image=image)
    record["Image"] = image
    record["HostConfig"]["NetworkMode"] = "bridge"
    assert backend.validate_inspection(record, "owned", image=image)


@pytest.mark.parametrize("image", ["python:latest", "python:3.14", "sha256:abc", "sha256:" + "A" * 64])
def test_dependency_images_reject_mutable_or_malformed_references(tmp_path: Path, image: str) -> None:
    with pytest.raises(ValueError, match="immutable local image ID"):
        backend.run_isolated(tmp_path, ["candidate.py"], {}, image=image)


def test_tfidf_profile_requires_task_resources() -> None:
    record = valid_inspection()
    assert backend.validate_inspection(record, "owned", "skillsbench-tfidf")
    record["HostConfig"].update(
        Memory=4096 * 1024 * 1024, MemorySwap=4096 * 1024 * 1024, NanoCpus=8_000_000_000, PidsLimit=256
    )
    assert backend.validate_inspection(record, "owned", "skillsbench-tfidf") == []
    assert backend.validate_inspection(record, "owned")


def test_mutation_profile_requires_bounded_private_semaphore_filesystem() -> None:
    record = valid_inspection()
    assert backend.validate_inspection(record, "owned", "python-mutation")
    record["HostConfig"]["Tmpfs"]["/dev/shm"] = "rw,noexec,nosuid,size=16m"
    assert backend.validate_inspection(record, "owned", "python-mutation") == []
    assert backend.validate_inspection(record, "owned")
    for value in ("rw,noexec,nosuid,size=128m", "rw,nosuid,size=16m", "rw,noexec,size=16m"):
        record["HostConfig"]["Tmpfs"]["/dev/shm"] = value
        assert backend.validate_inspection(record, "owned", "python-mutation")
    record["HostConfig"]["Tmpfs"]["/dev/shm"] = "rw,noexec,nosuid,size=16m"
    record["HostConfig"]["IpcMode"] = "host"
    assert backend.validate_inspection(record, "owned", "python-mutation")


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("NetworkMode", "bridge"),
        ("IpcMode", "host"),
        ("ReadonlyRootfs", False),
        ("Memory", 0),
        ("MemorySwap", -1),
        ("NanoCpus", 0),
        ("PidsLimit", -1),
        ("Privileged", True),
        ("Init", False),
        ("CapDrop", []),
        ("CapAdd", ["SYS_ADMIN"]),
        ("SecurityOpt", []),
        ("LogConfig", {"Type": "json-file"}),
        ("Tmpfs", {"/tmp": "rw,noexec,nosuid,size=256m"}),
        ("Devices", [{"PathOnHost": "/dev/sda"}]),
        ("VolumesFrom", ["foreign"]),
    ],
)
def test_inspection_rejects_weakened_constraints(key: str, value: Any) -> None:
    record = valid_inspection()
    record["HostConfig"][key] = value
    assert backend.validate_inspection(record, "owned")


def test_inspection_rejects_mounts_identity_and_images() -> None:
    original = valid_inspection()
    for change in ("writable", "extra", "user", "image", "owner"):
        record = copy.deepcopy(original)
        if change == "writable":
            record["Mounts"][0]["RW"] = True
        elif change == "extra":
            record["Mounts"].append({"Destination": "/oracle", "Type": "bind", "RW": False})
        elif change == "user":
            record["Config"]["User"] = "root"
        elif change == "image":
            record["Config"]["Image"] = "python:latest"
        else:
            record["Config"]["Labels"][backend.OWNER_LABEL] = "foreign"
        assert backend.validate_inspection(record, "owned")


@pytest.mark.parametrize(
    "path", ["", "/absolute.py", "../oracle.py", "a/../b.py", "a//b.py", "./a.py", "C:/a.py", "a\\b.py"]
)
def test_staging_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(ValueError):
        backend.relative_file(path)


def test_staging_copies_only_explicit_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "stage"
    source.mkdir()
    destination.mkdir()
    expected = b"def run(request):\n    return request\n"
    (source / "candidate.py").write_bytes(expected)
    (source / "oracle.txt").write_text("unmounted expected answer", encoding="utf-8")
    hashes = backend.stage_files(source, ["candidate.py"], destination)
    assert hashes == {"candidate.py": hashlib.sha256(expected).hexdigest()}
    assert sorted(path.name for path in destination.iterdir()) == ["candidate.py"]
    assert (destination / "candidate.py").read_bytes() == expected


def test_staging_rejects_case_collisions_and_oversize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destination = tmp_path / "stage"
    destination.mkdir()
    (tmp_path / "candidate.py").write_bytes(b"too large")
    with pytest.raises(ValueError, match="unique"):
        backend.stage_files(tmp_path, ["candidate.py", "CANDIDATE.py"], destination)
    monkeypatch.setattr(backend, "MAX_FILE_BYTES", 2)
    with pytest.raises(ValueError, match="size bound"):
        backend.stage_files(tmp_path, ["candidate.py"], destination)


def test_staging_rejects_links(tmp_path: Path) -> None:
    destination = tmp_path / "stage"
    destination.mkdir()
    original = tmp_path / "original.py"
    original.write_text("content", encoding="utf-8")
    link = tmp_path / "candidate.py"
    try:
        link.symlink_to(original)
    except OSError as exc:
        pytest.skip(f"host cannot create symlinks: {exc}")
    with pytest.raises(ValueError, match="link/reparse"):
        backend.stage_files(tmp_path, [link.name], destination)


@pytest.mark.parametrize(
    "raw",
    [
        b"plain output",
        b"{}",
        b"[]",
        b'{"worker_status":[]}',
        b'{"worker_status":"returned"}',
        b'{"worker_status":"returned","result":NaN}',
        b'{"worker_status":"returned","result":1,"result":2}',
        b'{"worker_status":"returned","result":1,"score":100}',
        b"\xff",
    ],
)
def test_response_rejects_invalid_envelopes(raw: bytes) -> None:
    with pytest.raises((ValueError, UnicodeError)):
        backend.parse_response(raw)


def test_response_retains_untrusted_result() -> None:
    assert backend.parse_response(b'{"worker_status":"returned","result":false}')["result"] is False


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), 601])
def test_invalid_timeouts_do_not_launch_docker(tmp_path: Path, timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout"):
        backend.run_isolated(tmp_path, ["candidate.py"], {}, timeout=timeout)


def test_missing_selected_entrypoint_does_not_launch(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="explicitly staged"):
        backend.run_isolated(tmp_path, ["other.py"], {})


def control_result(value: Any = 4) -> dict[str, Any]:
    inspection = valid_inspection()
    return {
        "status": "completed",
        "cleanup_verified": True,
        "scored": False,
        "candidate_response_is_untrusted": True,
        "candidate_response": {"worker_status": "returned", "result": value},
        "isolation_checks": {
            "passed": True,
            "errors": [],
            "observed_user": "65534:65534",
            "observed_image": backend.IMAGE,
            "observed_ownership_token": "owned",
            "observed_host_constraints": inspection["HostConfig"],
            "observed_mounts": inspection["Mounts"],
        },
    }


def test_control_oracle_rejects_wrong_answers_and_cleanup_failures() -> None:
    case = qualification.controls()[0]
    assert qualification.control_passes(case, control_result())
    assert not qualification.control_passes(case, control_result(999))
    result = control_result()
    result["cleanup_error"] = "transport still running"
    assert not qualification.control_passes(case, result)


def test_control_check_recomputes_observed_isolation() -> None:
    result = control_result()
    result["isolation_checks"]["observed_host_constraints"]["NetworkMode"] = "host"
    assert not qualification.control_passes(qualification.controls()[0], result)


def test_control_requires_real_integer_answer() -> None:
    assert not qualification.control_passes(qualification.controls()[0], control_result(4.0))


def test_control_receipt_rejects_incomplete_denominators() -> None:
    errors = qualification.validate_receipt(
        {
            "schema_version": 1,
            "evidence_class": "independent-container-backend-controls",
            "input_sha256": qualification.input_hashes(),
            "controls": [],
            "all_controls_passed": True,
        }
    )
    assert errors == ["incomplete control denominator"]


def test_control_receipt_rejects_forged_pass_markers() -> None:
    cases = qualification.controls()
    records = [
        {
            "control": case["control"],
            "code_sha256": hashlib.sha256(case["code"].encode()).hexdigest(),
            "expected_execution_status": case["expected_execution_status"],
            "passed": True,
            "execution": {"status": "completed", "cleanup_verified": True},
        }
        for case in cases
    ]
    errors = qualification.validate_receipt(
        {
            "schema_version": 1,
            "evidence_class": "independent-container-backend-controls",
            "input_sha256": qualification.input_hashes(),
            "controls": records,
            "all_controls_passed": True,
        }
    )
    assert len(errors) == len(cases)


def test_control_check_cli_reports_malformed_receipt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "receipt.json"
    path.write_text("[]", encoding="utf-8")
    assert qualification.main(["--output", str(path), "--check", "--json"]) == 1
    assert "receipt must be an object" in capsys.readouterr().out


@pytest.mark.parametrize("foreign_owner", [False, True])
def test_failed_inspection_cleans_only_verified_owned_container(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    foreign_owner: bool,
) -> None:
    (tmp_path / "candidate.py").write_text("def run(request): return 4", encoding="utf-8")
    calls: list[list[str]] = []
    identity: dict[str, str] = {}
    container_id = "1" * 64

    def fake_docker(arguments: list[str], *, timeout: float = 15) -> subprocess.CompletedProcess[bytes]:
        calls.append(arguments)
        if arguments[0] == "create":
            identity["token"] = arguments[arguments.index("--label") + 1].split("=", 1)[1]
            identity["name"] = arguments[arguments.index("--name") + 1]
            return subprocess.CompletedProcess(arguments, 0, (container_id + "\n").encode(), b"")
        if arguments[0] == "inspect":
            assert arguments[1] in {container_id, identity["name"]}
            record = valid_inspection()
            record["Id"] = container_id
            record["Config"]["Labels"][backend.OWNER_LABEL] = "foreign" if foreign_owner else identity["token"]
            record["HostConfig"]["NetworkMode"] = "host"
            return subprocess.CompletedProcess(arguments, 0, json.dumps([record]).encode(), b"")
        if arguments[0] == "rm":
            assert not foreign_owner
            assert arguments == ["rm", "--force", container_id]
            return subprocess.CompletedProcess(arguments, 0, container_id.encode(), b"")
        assert arguments == [
            "ps",
            "--all",
            "--quiet",
            "--filter",
            "label=" + backend.OWNER_LABEL + "=" + identity["token"],
        ]
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    monkeypatch.setattr(backend, "docker_call", fake_docker)
    result = backend.run_isolated(tmp_path, ["candidate.py"], {})
    assert result["status"] == "infrastructure_error"
    assert "constraints failed inspection" in result["detail"]
    assert result["cleanup_verified"] is not foreign_owner
    assert not any(call[0] == "start" for call in calls)
    assert any(call[0] == "rm" for call in calls) is not foreign_owner
