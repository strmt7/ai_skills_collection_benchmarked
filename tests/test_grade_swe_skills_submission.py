from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import grade_swe_skills_submission as controller
import pytest
from _trial_collection_policy import default_collection_policy


def test_native_restore_support_imports_without_checkout_or_site_packages(tmp_path):
    for name in controller.SUPPORT:
        shutil.copyfile(controller.ROOT / "tools" / name, tmp_path / name)
    probe = "import sys;sys.path.insert(0,sys.argv[1]);from transfer_benchmark_submission import plan_handoff,restore;print('NATIVE_RESTORE_IMPORTS_READY')"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-S", "-c", probe, str(tmp_path)],
        cwd=tmp_path,
        capture_output=True,
        check=True,
        timeout=10,
    )
    assert result.stdout.strip() == b"NATIVE_RESTORE_IMPORTS_READY" and not result.stderr


def _asset(path: Path, data: bytes, **extra: Any) -> dict[str, Any]:
    path.write_bytes(data)
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), **extra}


@pytest.fixture
def frozen_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    monkeypatch.setattr(controller, "source_hashes", lambda: {"tools/controller.py": "f" * 64})
    inventory = {
        "schema_version": 1,
        "pytest_version": "9.0.2",
        "rootdir": "/workspace",
        "min_pass_rate": 1.0,
        "cases": {"../tests/test_fixture.py::test_case": "tests.test_fixture::test_case"},
    }
    return {
        "schema_version": 2,
        "id": "public-development-fixture",
        "source": {"repository": "publisher/project", "commit": "a" * 40},
        "collection_policy": default_collection_policy(),
        "baseline_manifest_sha256": "b" * 64,
        "image_reference": "docker.io/publisher/fixture@sha256:" + "c" * 64,
        "source_directory": "fixture",
        "import_paths": ["src"],
        "grader_user": "dev",
        "test_timeout_seconds": 30,
        "min_pass_rate": 1.0,
        "verifier": _asset(tmp_path / "test_fixture.py", b"trusted verifier", target="test_fixture.py"),
        "inventory": _asset(tmp_path / "inventory.json", json.dumps(inventory).encode()),
        "scorer": {
            "files": [_asset(tmp_path / "scorer.py", b"trusted scorer", target="src/evaluator.py")],
            "wheels": [
                _asset(
                    tmp_path / "fixture-1.0-py3-none-any.whl", b"frozen test artifact", project="fixture", version="1.0"
                )
            ],
            "versions": {"fixture": "1.0"},
        },
        "execution_source_sha256": controller.source_hashes(),
        "python_safe_path": True,
        "import_origins": {
            "pytest": {"image_path": "/usr/lib/python/site-packages/pytest/__init__.py", "sha256": "a" * 64},
            "project": {"source_path": "src/project/__init__.py"},
        },
    }


def test_frozen_native_task_admits_explicit_assets_and_root_import(
    frozen_task: dict[str, Any],
) -> None:
    frozen_task["import_paths"] = ["."]
    assert controller.validate_task(frozen_task) is frozen_task


@pytest.mark.parametrize("timeout", [300, 600, 900])
def test_publisher_test_deadlines_are_preserved(frozen_task: dict[str, Any], timeout: int) -> None:
    frozen_task["test_timeout_seconds"] = timeout
    assert controller.validate_task(frozen_task)["test_timeout_seconds"] == timeout


@pytest.mark.parametrize("timeout", [True, 0, 901, 600.0])
def test_test_deadline_must_be_a_supported_integer(frozen_task: dict[str, Any], timeout: Any) -> None:
    frozen_task["test_timeout_seconds"] = timeout
    with pytest.raises(ValueError, match="runtime profile"):
        controller.validate_task(frozen_task)


@pytest.mark.parametrize(
    "change", ["controller", "verifier", "inventory_threshold", "wheel_collision", "source_revision"]
)
def test_native_task_rejects_changed_sources_or_ambiguous_inputs(frozen_task: dict[str, Any], change: str) -> None:
    if change == "controller":
        frozen_task["execution_source_sha256"] = {}
    elif change == "verifier":
        Path(frozen_task["verifier"]["path"]).write_bytes(b"changed verifier")
    elif change == "inventory_threshold":
        frozen_task["min_pass_rate"] = 0.5
    elif change == "wheel_collision":
        duplicate = {**frozen_task["scorer"]["wheels"][0], "project": "other"}
        frozen_task["scorer"]["wheels"].append(duplicate)
        frozen_task["scorer"]["versions"]["other"] = "1.0"
    else:
        frozen_task["source"]["commit"] = "mutable-main"
    with pytest.raises(ValueError):
        controller.validate_task(frozen_task)


def test_incomplete_capture_returns_no_score_before_native_runtime(
    tmp_path: Path, frozen_task: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(controller, "ROOT", tmp_path)
    (tmp_path / ".venv").mkdir()
    called = []

    def incomplete(*args: Any) -> Any:
        raise ValueError("Source collection process did not complete")

    monkeypatch.setattr(controller, "completed_capture", incomplete)
    monkeypatch.setattr(controller, "DockerClient", lambda *args: called.append(args))
    result = controller.grade(
        frozen_task,
        tmp_path / "runtime.json",
        tmp_path / "baseline",
        tmp_path / "subject",
        tmp_path / ".venv" / "result",
    )
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "validate"
    assert called == []
    saved = json.loads((tmp_path / ".venv/result/result.json").read_bytes())
    assert saved == result


def test_existing_grade_output_is_preserved(
    tmp_path: Path, frozen_task: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(controller, "ROOT", tmp_path)
    output = tmp_path / ".venv/previous"
    output.mkdir(parents=True)
    marker = output / "result.json"
    marker.write_bytes(b"previous evidence")
    with pytest.raises(ValueError, match="new directory"):
        controller.grade(frozen_task, tmp_path / "runtime", tmp_path / "base", tmp_path / "subject", output)
    assert marker.read_bytes() == b"previous evidence"


@pytest.mark.parametrize(
    "change", ["undeclared_path_mode", "missing_framework", "framework_from_source", "missing_project"]
)
def test_native_task_requires_explicit_framework_and_project_origins(frozen_task: dict[str, Any], change: str) -> None:
    if change == "undeclared_path_mode":
        frozen_task["python_safe_path"] = "enabled"
    elif change == "missing_framework":
        del frozen_task["import_origins"]["pytest"]
    elif change == "framework_from_source":
        frozen_task["import_origins"]["pytest"] = {"source_path": "pytest.py"}
    else:
        del frozen_task["import_origins"]["project"]
    with pytest.raises(ValueError):
        controller.validate_task(frozen_task)


def _with_environment(task: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    task.update(
        schema_version=3,
        python_environment={
            "schema_version": 1,
            "python_version": "3.12.3",
            "machine": "x86_64",
            "wheels": [
                _asset(tmp_path / f"{name}-{version}-py3-none-any.whl", name.encode(), project=name, version=version)
                for name, version in (("pip", "26.3"), ("pytest", "9.0.2"))
            ],
            "resources": {"memory_bytes": 1024**3, "tmpfs_bytes": 256 * 1024**2},
            "setup_timeout_seconds": 120,
        },
    )
    task["import_origins"]["pytest"] = {
        "environment_path": "lib/python3.12/site-packages/pytest/__init__.py",
        "sha256": "a" * 64,
    }
    return task


def test_frozen_environment_admits_exact_graph_and_stages_hash_locks(frozen_task, tmp_path):
    task = _with_environment(frozen_task, tmp_path)
    assert controller.validate_task(task) is task
    packet = controller.environment_packet(task["python_environment"], controller.asset)
    assert packet["grader-wheels/pytest-9.0.2-py3-none-any.whl"] == b"pytest"
    assert b"pytest==9.0.2 --hash=sha256:" in packet["grader-requirements.lock"]
    assert (
        packet["tools/_native_grader_dependencies.py"]
        == (controller.ROOT / "tools/_native_grader_dependencies.py").read_bytes()
    )
    task["schema_version"] = 2
    with pytest.raises(ValueError, match="complete frozen"):
        controller.validate_task(task)


def test_guest_interpreter_and_import_paths_stay_posix_on_windows_controllers():
    assert controller.DEPENDENCY_PYTHON == "/tmp/grader-dependencies/bin/python"
    assert str(controller.DEPENDENCY_PREFIX / "lib/python3.12/site-packages/pytest/__init__.py") == (
        "/tmp/grader-dependencies/lib/python3.12/site-packages/pytest/__init__.py"
    )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-pip",
        "duplicate",
        "changed-wheel",
        "escape",
        "image-framework",
        "pytest-version",
        "timeout",
        "memory",
        "architecture",
    ],
)
def test_frozen_environment_rejects_invalid_graph_or_runtime(frozen_task, tmp_path, mutation):
    task = _with_environment(frozen_task, tmp_path)
    spec = task["python_environment"]
    if mutation == "missing-pip":
        spec["wheels"].pop(0)
    elif mutation == "duplicate":
        spec["wheels"].append(dict(spec["wheels"][0]))
    elif mutation == "changed-wheel":
        Path(spec["wheels"][0]["path"]).write_bytes(b"changed")
    elif mutation == "escape":
        task["import_origins"]["pytest"]["environment_path"] = "../pytest.py"
    elif mutation == "image-framework":
        task["import_origins"]["pytest"] = {"image_path": "/usr/lib/pytest.py", "sha256": "a" * 64}
    elif mutation == "pytest-version":
        spec["wheels"][1]["version"] = "9.1.0"
    elif mutation == "timeout":
        spec["setup_timeout_seconds"] = True
    elif mutation == "memory":
        spec["resources"]["memory_bytes"] = True
    else:
        spec["machine"] = "unobserved-host"
    with pytest.raises(ValueError):
        controller.validate_task(task)
