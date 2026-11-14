"""Dependency setup controls run without downloads, package imports or native executables."""

from __future__ import annotations

import json
from pathlib import Path

import prepare_subject_dependencies as dependencies
import pytest
from _native_benchmark_runtime import sha256


@pytest.fixture
def specification():
    return {
        "schema_version": 1,
        "python_version": "3.14.10",
        "architecture": "AMD64",
        "imports": ["fixture"],
        "packages": [
            {
                "name": "fixture",
                "version": "1.0",
                "extras": [],
                "filename": "fixture-1.0-py3-none-any.whl",
                "url": "https://files.pythonhosted.org/packages/fixture.whl",
                "bytes": 5,
                "sha256": sha256(b"wheel"),
            }
        ],
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("architecture", "ARM64"),
        ("python_version", "host"),
        ("imports", ["fixture;print('invalid')"]),
        ("packages", []),
    ],
)
def test_malformed_dependency_profiles_are_rejected(specification, field, value):
    specification[field] = value
    with pytest.raises(ValueError):
        dependencies.load_specification(json.dumps(specification).encode())


@pytest.mark.parametrize(
    "field,value",
    [
        ("filename", "../fixture.whl"),
        ("url", "https://unrelated.invalid/fixture.whl"),
        ("version", "1.0 --no-deps"),
        ("name", "Fixture"),
        ("extras", ["x", "x"]),
        ("sha256", "unfrozen"),
        ("bytes", True),
        ("bytes", 16 * 1024**2 + 1),
    ],
)
def test_invalid_wheel_inputs_are_rejected(specification, field, value):
    specification["packages"][0][field] = value
    with pytest.raises(ValueError):
        dependencies.load_specification(json.dumps(specification).encode())


def test_duplicate_packages_are_rejected(specification):
    specification["packages"] *= 2
    with pytest.raises(ValueError, match="repeated"):
        dependencies.load_specification(json.dumps(specification).encode())


@pytest.mark.parametrize("mutation", ["file", "directory", "delete"])
def test_profile_verification_detects_complete_namespace_drift(tmp_path, mutation):
    packages = tmp_path / "packages"
    packages.mkdir()
    module = packages / "fixture.py"
    module.write_bytes(b"original")
    receipt = {"packages": str(packages), "inventory": dependencies.inventory(packages)}
    assert dependencies.verify(receipt) == packages
    if mutation == "file":
        module.write_bytes(b"modified")
    elif mutation == "directory":
        (packages / "extra-empty-directory").mkdir()
    else:
        module.unlink()
    with pytest.raises(ValueError, match="changed"):
        dependencies.verify(receipt)


@pytest.mark.parametrize("budget", ["MAX_FILES", "MAX_BYTES"])
def test_inventory_is_bounded(tmp_path, monkeypatch, budget):
    (tmp_path / "fixture").write_bytes(b"xx")
    monkeypatch.setattr(dependencies, budget, 0)
    with pytest.raises(ValueError, match="budget"):
        dependencies.inventory(tmp_path)


@pytest.fixture
def setup(tmp_path, monkeypatch, specification):
    monkeypatch.setattr(dependencies, "ROOT", tmp_path)
    python, installer = tmp_path / "python/python.exe", tmp_path / "uv/uv.exe"
    for path in (python, installer):
        path.parent.mkdir()
        path.write_bytes(b"admitted unit fixture")
    monkeypatch.setattr(dependencies, "installer_identity", lambda path: {"version": "fixture"})
    calls = []

    def capture(item, archive_dir):
        calls.append(("capture", archive_dir))
        return b"wheel"

    def phase(output, label, argv, environment):
        calls.append((label, argv))
        assert "UNSELECTED_CREDENTIAL" not in environment and "PYTHONPATH" not in environment
        assert Path(environment["HOME"]).is_relative_to(output)
        if label == "install":
            assert all(flag in argv for flag in ("--offline", "--no-config", "--require-hashes", "--no-index"))
            assert argv[0] == str(installer) and argv[argv.index("--python") + 1] == str(python)
            target = Path(argv[argv.index("--target") + 1])
            target.mkdir()
            (target / "fixture.py").write_bytes(b"qualified unit fixture")
        else:
            assert argv[:3] == [str(python), "-I", "-B"]
            assert "--require-package-imports" in argv
            (output / "check.stdout.native").write_text(
                json.dumps(
                    {
                        "python": "3.14.10",
                        "implementation": "cpython",
                        "bits": 64,
                        "os": "Windows",
                        "machine": "AMD64",
                    }
                ),
                encoding="utf-8",
            )

    monkeypatch.setenv("UNSELECTED_CREDENTIAL", "unselected unit fixture")
    monkeypatch.setenv("PYTHONPATH", "unselected-host-packages")
    monkeypatch.setenv("SYSTEMROOT", str(tmp_path / "system"))
    monkeypatch.setattr(dependencies, "capture", capture)
    monkeypatch.setattr(dependencies, "_phase", phase)
    return python, installer, tmp_path / ".venv/setup", calls


def test_normal_install_uses_only_explicit_inputs_and_private_profiles(specification, setup):
    python, installer, output, calls = setup
    raw = json.dumps(specification).encode()
    receipt = dependencies.prepare(raw, python, installer, output)
    assert dependencies.verify(receipt) == output / "packages"
    assert (output / "specification.json").read_bytes() == raw
    assert receipt["specification_sha256"] == sha256(raw)
    assert [call[0] for call in calls] == ["capture", "install", "check"]
    with pytest.raises(FileExistsError):
        dependencies.prepare(raw, python, installer, output)


def test_space_budget_reaches_both_owned_setup_phases(specification, setup, tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    python, installer, output, calls = setup
    monkeypatch.setattr(
        storage,
        "available_space",
        lambda _path: {"available_bytes": 1000, "total_bytes": 2000, "volume_free_bytes": 1000},
    )
    budget = storage.SpaceBudget(storage.StorageLimits(10, 1024, 100), (tmp_path,))
    original = dependencies._phase
    phases = []

    def monitored(output, label, argv, environment, *, space_budget):
        assert space_budget is budget
        space_budget.require_available()
        phases.append(label)
        return original(output, label, argv, environment)

    monkeypatch.setattr(dependencies, "_phase", monitored)
    dependencies.prepare(json.dumps(specification).encode(), python, installer, output, space_budget=budget)
    assert phases == ["install", "check"] and budget.record()["polls"] >= 5
    assert calls[0][0] == "capture"


def test_space_lost_during_wheel_capture_prevents_installer_start(specification, setup, tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    python, installer, output, calls = setup
    monkeypatch.setattr(
        storage,
        "available_space",
        lambda _path: {"available_bytes": 5 if calls else 1000, "total_bytes": 2000, "volume_free_bytes": 1000},
    )
    budget = storage.SpaceBudget(storage.StorageLimits(10, 1024, 100), (tmp_path,))
    with pytest.raises(ValueError, match="free_space_limit"):
        dependencies.prepare(json.dumps(specification).encode(), python, installer, output, space_budget=budget)
    assert [call[0] for call in calls] == ["capture"]
    assert not (output / "receipt.json").exists() and budget.reason == "free_space_limit"


def test_missing_local_wheel_uses_its_exact_official_download(specification, setup, tmp_path):
    python, installer, output, calls = setup
    archives = tmp_path / "archives"
    archives.mkdir()
    dependencies.prepare(json.dumps(specification).encode(), python, installer, output, archive_dir=archives)
    assert calls[0] == ("capture", None)


def test_dependency_setup_refuses_output_over_existing_inputs(specification, setup):
    python, installer, output, calls = setup
    with pytest.raises(ValueError, match="fresh owned"):
        dependencies.prepare(json.dumps(specification).encode(), python, installer, python.parent)
    assert calls == []


@pytest.mark.parametrize("failure", ["exit_code", "termination_reason", "job_active_processes_after_cleanup"])
def test_failed_owned_installation_preserves_native_evidence_without_a_receipt(tmp_path, monkeypatch, failure):
    observed: dict[str, int | str | None] = {
        "exit_code": 0,
        "termination_reason": None,
        "job_active_processes_after_cleanup": 0,
    }
    observed[failure] = "output_limit" if failure == "termination_reason" else 1

    def process(argv, **kwargs):
        kwargs["stderr"].write(b"owned native failure")
        return observed

    monkeypatch.setattr(dependencies, "run_owned", process)
    with pytest.raises(ValueError, match="retained diagnostics"):
        dependencies._phase(tmp_path, "install", ["forbidden-unit-executable"], {})
    assert json.loads((tmp_path / "install.process.json").read_bytes()) == observed
    assert (tmp_path / "install.stderr.native").read_bytes() == b"owned native failure"
    assert not (tmp_path / "receipt.json").exists()


def test_actual_installer_bytes_must_match_the_repository_pin(tmp_path, monkeypatch):
    binary = tmp_path / "uv.exe"
    binary.write_bytes(b"admitted unit executable")
    manifest = tmp_path / "toolchains/bootstrap/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "uv": {
                    "version": "fixture",
                    "files": {
                        "uv.exe": {
                            "bytes": binary.stat().st_size,
                            "sha256": sha256(binary.read_bytes()),
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(dependencies, "ROOT", tmp_path)
    assert dependencies.installer_identity(binary)["version"] == "fixture"
    binary.write_bytes(b"x" * binary.stat().st_size)
    with pytest.raises(ValueError, match="qualified UV"):
        dependencies.installer_identity(binary)


def test_wrong_actual_python_cannot_publish_a_ready_profile(specification, setup, monkeypatch):
    python, installer, output, _ = setup
    original = dependencies._phase

    def wrong_runtime(*args):
        original(*args)
        if args[1] == "check":
            data = json.loads((output / "check.stdout.native").read_bytes())
            data["python"] = "3.13.18"
            (output / "check.stdout.native").write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(dependencies, "_phase", wrong_runtime)
    with pytest.raises(ValueError, match="frozen interpreter"):
        dependencies.prepare(json.dumps(specification).encode(), python, installer, output)
    assert (output / "check.stdout.native").exists()
    assert not (output / "receipt.json").exists()
