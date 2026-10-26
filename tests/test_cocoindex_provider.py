"""Enforce provider provenance, safe model files and isolated cache boundaries."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from types import SimpleNamespace

import cocoindex_runtime as runtime
import cocoindex_tool as launcher
import prepare_cocoindex_source as source
import pytest
import verify_cocoindex_wheel as wheel


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def admitted(tmp_path):
    root = tmp_path / "repo"
    directory = root / "toolchains/cocoindex-code"
    directory.mkdir(parents=True)
    license_bytes, notice = b"complete fixture license", b"explicit local-only change notice"
    (directory / "LICENSE").write_bytes(license_bytes)
    (directory / "CATALOG_BUILD_NOTICE.txt").write_bytes(notice)
    version = "0.2.42+catalog.local1"
    prefix = "cocoindex_code-" + version + ".dist-info/"
    members = {
        "cocoindex_code/client.py": b"# opaque fixture; never imported\n",
        "cocoindex_code/CATALOG_BUILD_NOTICE.txt": notice,
        prefix + "licenses/LICENSE": license_bytes,
        prefix + "METADATA": (
            "Name: cocoindex-code\nVersion: " + version + "\nRequires-Dist: cocoindex>=1.0.17\n\n"
        ).encode(),
    }
    candidate = root / "fixture.whl"
    with zipfile.ZipFile(candidate, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
    original_lock = "cocoindex-code[embeddings-local]==0.2.42 --hash=sha256:" + "0" * 64 + "\n"
    (directory / "requirements.txt").write_text(original_lock, encoding="utf-8")
    wheel_hash = sha(candidate.read_bytes())
    derived = "cocoindex-code[embeddings-local]==" + version + " --hash=sha256:" + wheel_hash + "\n"
    pin = {
        "version": version,
        "upstream_version": "0.2.42",
        "qualified_wheel_sha256": wheel_hash,
        "runtime_files": [
            {"path": name, "sha256": sha(raw)} for name, raw in members.items() if name.startswith("cocoindex_code/")
        ],
        "core": {"runtime_files": [{"path": "cocoindex/engine.pyd", "sha256": sha(b"opaque native fixture")}]},
        "runtime_versions": {"cocoindex-code": version, "cocoindex": "1.0.26", "pip": "26.2.2"},
        "qualified_runtime_lock_sha256": sha(derived.encode()),
        "advisory_coordinate_mapping": {"cocoindex-code": {"installed": version, "audited_source": "0.2.42"}},
    }
    (directory / "source.json").write_text(json.dumps(pin), encoding="utf-8")
    return root, directory, candidate, pin, members


def test_admitted_install_lock_has_portable_lines_and_keeps_public_advisory_coordinates(admitted):
    root, directory, candidate, pin, _ = admitted
    original = (directory / "requirements.txt").read_bytes()
    stage = root / ".venv/admission"
    assert wheel.prepare(root, candidate, stage)["ok"]
    assert wheel.prepare(root, candidate, stage, check=True)["ok"]
    generated = (stage / "requirements.txt").read_bytes()
    assert b"\r\n" not in generated and sha(generated) == pin["qualified_runtime_lock_sha256"]
    assert (directory / "requirements.txt").read_bytes() == original
    with pytest.raises(FileExistsError):
        wheel.prepare(root, candidate, stage)
    (stage / "unexpected.py").write_bytes(b"unadmitted file")
    with pytest.raises(ValueError, match="stage differs"):
        wheel.prepare(root, candidate, stage, check=True)


@pytest.mark.parametrize(
    "change,expected", [("source", "runtime sources"), ("license", "license"), ("cloud", "cloud embedding")]
)
def test_updated_archive_digest_cannot_launder_changed_code_license_or_cloud_metadata(admitted, change, expected):
    root, directory, candidate, pin, members = admitted
    if change == "source":
        members["cocoindex_code/client.py"] = b"# changed source\n"
    elif change == "license":
        name = [name for name in members if name.endswith("licenses/LICENSE")][0]
        members[name] = b"incomplete license"
    else:
        name = [name for name in members if name.endswith("/METADATA")][0]
        members[name] += b"Requires-Dist: cocoindex[litellm]>=1.0.17\n"
        members[name] = members[name].replace(b"\n\nRequires-Dist:", b"\nRequires-Dist:")
    with zipfile.ZipFile(candidate, "w") as archive:
        for name, raw in members.items():
            archive.writestr(name, raw)
    pin["qualified_wheel_sha256"] = sha(candidate.read_bytes())
    (directory / "source.json").write_text(json.dumps(pin), encoding="utf-8")
    with pytest.raises(ValueError, match=expected):
        wheel.verify_wheel(root, candidate)


@pytest.mark.parametrize("change", ["changed-core", "missing-core", "external-location", "extra-distribution"])
def test_installed_provider_core_and_full_dependency_graph_are_admitted(admitted, monkeypatch, change):
    root, _, _, pin, members = admitted
    prefix = root / ".venv/runtime"
    providers = prefix / "Lib/site-packages"
    for name, raw in members.items():
        if name.startswith("cocoindex_code/"):
            target = providers / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    core = providers / "cocoindex/engine.pyd"
    core.parent.mkdir(parents=True)
    if change != "missing-core":
        core.write_bytes(b"changed native fixture" if change == "changed-core" else b"opaque native fixture")
    versions = {**pin["runtime_versions"]}
    if change == "extra-distribution":
        versions["unadmitted-package"] = "1.0"
    monkeypatch.setattr(wheel, "installed_versions", lambda: versions)
    monkeypatch.setattr(wheel.sys, "prefix", str(prefix))
    distribution = SimpleNamespace(
        locate_file=lambda name: root / "foreign.py" if change == "external-location" else providers / name
    )
    monkeypatch.setattr(wheel.importlib.metadata, "distribution", lambda _name: distribution)
    with pytest.raises(ValueError, match="provider source|dependency versions"):
        wheel.installed_files(pin)


@pytest.fixture
def local_model(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    home = root / ".venv/provider"
    model = home / "model"
    model.mkdir(parents=True)
    modules = [{"type": "sentence_transformers.models." + name} for name in ["Transformer", "Pooling", "Normalize"]]
    contents = {
        "model.safetensors": b"opaque model fixture; never loaded",
        "modules.json": json.dumps(modules).encode(),
    }
    for name, raw in contents.items():
        (model / name).write_bytes(raw)
    proof = {
        "model": "fixtures/local-model",
        "revision": "a" * 40,
        "custom_code_present": False,
        "modules": modules,
        "files": [{"path": name, "sha256": sha(raw)} for name, raw in contents.items()],
        "file_sizes": {name: len(raw) for name, raw in contents.items()},
    }
    directory = root / "toolchains/cocoindex-code"
    directory.mkdir(parents=True)
    (directory / "model.json").write_text(json.dumps(proof), encoding="utf-8")
    monkeypatch.setattr(runtime, "ROOT", root)
    return root, home, proof


@pytest.mark.parametrize("change", ["changed-bytes", "extra-code", "empty-linked-directory"])
def test_model_admission_rejects_tampering_extra_code_and_linked_directories(local_model, monkeypatch, change):
    _, home, _ = local_model
    assert runtime.check_model(home)["model_files_admitted"] == 2
    if change == "changed-bytes":
        target = home / "model/model.safetensors"
        target.write_bytes(b"x" * target.stat().st_size)
    elif change == "extra-code":
        (home / "model/custom.py").write_text("raise RuntimeError('unadmitted')", encoding="utf-8")
    else:
        path = home / "model/linked"
        path.mkdir()
        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda candidate: candidate == path or original(candidate))
    with pytest.raises(ValueError, match="changed model|inventory|link"):
        runtime.check_model(home)


@pytest.mark.parametrize("change", ["custom-flag", "custom-module", "pickle-weights"])
def test_model_contract_refuses_custom_modules_and_executable_weight_formats(local_model, change):
    root, _, proof = local_model
    if change == "custom-flag":
        proof["custom_code_present"] = True
    elif change == "custom-module":
        proof["modules"][0]["type"] = "untrusted.Model"
    else:
        for entry in proof["files"]:
            if entry["path"] == "model.safetensors":
                entry["path"] = "weights.bin"
    (root / "toolchains/cocoindex-code/model.json").write_text(json.dumps(proof), encoding="utf-8")
    with pytest.raises(ValueError, match="custom model|built-in|safe tensor"):
        runtime.model_proof()


def test_model_hash_records_reject_duplicate_paths(local_model):
    root, home, proof = local_model
    assert runtime.check_model(home)["model_files_admitted"] == 2
    proof["files"].append(proof["files"][0].copy())
    (root / "toolchains/cocoindex-code/model.json").write_text(json.dumps(proof), encoding="utf-8")
    with pytest.raises(ValueError, match="unique files"):
        runtime.check_model(home)


@pytest.mark.parametrize("change", ["revision", "size"])
def test_model_metadata_is_checked_without_personal_tokens_before_download(local_model, monkeypatch, change):
    _, home, proof = local_model
    fresh = home.parent / "fresh"
    fresh.mkdir()
    downloads = []

    def metadata(_url, **kwargs):
        assert kwargs["token"] is False and kwargs["retry_on_errors"] is False and kwargs["timeout"] == 30
        return SimpleNamespace(
            commit_hash="b" * 40 if change == "revision" else proof["revision"], size=-1, etag="fixture"
        )

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(
            hf_hub_url=lambda *args, **kwargs: "https://huggingface.co/fixtures/pinned",
            get_hf_file_metadata=metadata,
            hf_hub_download=lambda *args, **kwargs: downloads.append(args),
        ),
    )
    with pytest.raises(ValueError, match="pinned revision or size"):
        runtime.install_model(fresh)
    assert not downloads


def test_missing_index_check_does_not_prepare_or_create_a_corpus(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    monkeypatch.setattr(runtime, "ROOT", root)
    target = root / ".venv/new-corpus"
    with pytest.raises(ValueError, match="must already exist"):
        runtime.index(root / ".venv/provider", target, ["known.py"], check=True)
    assert not target.exists()


def test_index_check_waits_for_the_native_startup_scan(monkeypatch):
    states = [
        {"indexing": True, "index_exists": True, "progress": {"num_errors": 0}},
        {"indexing": False, "index_exists": True, "progress": None},
    ]
    observed = []

    def project_status(path):
        observed.append(path)
        return states.pop(0)

    client = SimpleNamespace(project_status=project_status)
    monkeypatch.setitem(sys.modules, "msgspec", SimpleNamespace(to_builtins=lambda value: value))
    monkeypatch.setitem(sys.modules, "cocoindex_code", SimpleNamespace(client=client))
    monkeypatch.setitem(sys.modules, "cocoindex_code.client", client)
    monkeypatch.setattr(runtime.time, "sleep", lambda delay: observed.append(delay))
    result = runtime.wait_for_index(Path("fixture-tree"))
    assert result["index_exists"] and result["indexing"] is False
    assert observed == ["fixture-tree", 0.1, "fixture-tree"]


@pytest.mark.parametrize("change", ["timeout", "missing-index", "index-errors"])
def test_native_index_checks_fail_on_timeouts_missing_indexes_or_errors(monkeypatch, change):
    status = {
        "indexing": change == "timeout",
        "index_exists": change != "missing-index",
        "progress": {"num_errors": int(change == "index-errors")},
    }
    client = SimpleNamespace(project_status=lambda _path: status)
    monkeypatch.setitem(sys.modules, "msgspec", SimpleNamespace(to_builtins=lambda value: value))
    monkeypatch.setitem(sys.modules, "cocoindex_code", SimpleNamespace(client=client))
    monkeypatch.setitem(sys.modules, "cocoindex_code.client", client)
    monkeypatch.setattr(runtime.time, "sleep", lambda _delay: pytest.fail("An expired check must not wait"))
    with pytest.raises((TimeoutError, ValueError), match="deadline|error-free index"):
        runtime.wait_for_index(Path("fixture-tree"), timeout=0)


def test_explicit_foreign_provider_path_is_rejected_before_reading_provider_pins(tmp_path):
    with pytest.raises(ValueError, match="dedicated directory"):
        launcher.home_path(tmp_path, tmp_path / "other-application")
    assert not list(tmp_path.iterdir())


def test_source_stage_preserves_failed_checks_and_refuses_replacement(tmp_path, monkeypatch):
    pin = {
        "upstream_version": "0.2.42",
        "version": "0.2.42+catalog.local1",
        "original_source_sha256": {"source.py": "original"},
    }
    contents = {"source.py": b"# admitted fixture bytes\n"}
    monkeypatch.setattr(source, "inputs", lambda *args: (pin, contents))
    stage = tmp_path / ".venv/source"
    assert source.prepare(tmp_path, tmp_path / "unused-archive", stage)["ok"]
    with pytest.raises(FileExistsError):
        source.prepare(tmp_path, tmp_path / "unused-archive", stage)
    (stage / "source.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="exact admitted inventory"):
        source.prepare(tmp_path, tmp_path / "unused-archive", stage, check=True)
    assert (stage / "source.py").read_bytes() == b"changed"


def test_isolated_public_help_ignores_foreign_provider_modules(tmp_path):
    (tmp_path / "prepare_cocoindex_source.py").write_text("raise RuntimeError('foreign import')", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", str(Path(launcher.__file__)), "--help"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert b"{setup,check,index,search}" in result.stdout
