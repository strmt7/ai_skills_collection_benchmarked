"""Frozen local metadata must not silently alter archived or active agent conditions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import _trial_catalog as catalogs
import pytest
import qualify_native_trial_boundary as boundary
from _trial_context import TrialContext, command

PROVIDER = {"authentication": "none", "base_url": "http://127.0.0.1:8123/v1"}
MODEL = "owned-local-model"


def reference(path, data):
    path.write_bytes(data)
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest()}


@pytest.fixture
def declared(tmp_path):
    model = {"slug": MODEL, "context_window": 65536, "base_instructions": "Owned native baseline instructions.\r\n"}
    entry = reference(tmp_path / "catalog.json", json.dumps({"models": [model]}).encode())
    context = TrialContext(
        tmp_path / "controller",
        tmp_path / "workspace",
        tmp_path / "runtime/codex.exe",
        tmp_path / "python/python.exe",
        (tmp_path / "runtime", tmp_path / "python"),
        {},
        {},
    )
    return entry, context, model


def test_local_metadata_is_explicit_and_preserves_original_context(declared):
    entry, context, _ = declared
    local = catalogs.load_local_catalog(entry)
    with catalogs.catalog_lease(context, PROVIDER, local=local) as selected:
        assert selected.local_catalog is local and context.local_catalog is None
        invocation = command(selected, MODEL, "high", provider=PROVIDER)
        assert "model_catalog_json=" + json.dumps(entry["path"]) in invocation
        assert "--ignore-user-config" in invocation
    assert local.metadata()["base_instructions"].endswith("\r\n")


@pytest.mark.parametrize("phase", ["before", "during"])
@pytest.mark.parametrize("fault", ["missing", "same-size", "growth"])
def test_changed_catalog_is_not_admitted_or_scored_as_unchanged(declared, phase, fault):
    entry, context, _ = declared
    local = catalogs.load_local_catalog(entry)

    def change():
        path = local.path()
        actual = Path(str(path))
        if fault == "missing":
            actual.unlink()
        else:
            original = actual.read_bytes()
            actual.write_bytes(b"x" * len(original) if fault == "same-size" else original + b"x")

    if phase == "before":
        change()
    with pytest.raises((ValueError, OSError)), catalogs.catalog_lease(context, PROVIDER, local=local):
        if phase == "during":
            change()
        else:
            pytest.fail("A changed catalog entered its lease")


def test_local_record_replays_without_original_host_files(declared):
    entry, _, _ = declared
    local = catalogs.load_local_catalog(entry)
    record = local.record()
    Path(entry["path"]).unlink()
    assert catalogs.decode_local_record(record) == local
    record["content"] += " "
    with pytest.raises(ValueError, match="identity"):
        catalogs.decode_local_record(record)


@pytest.mark.parametrize("fault", ["empty", "ambiguous", "boolean-window", "no-slug", "conflicting", "messages"])
def test_invalid_or_ambiguous_model_metadata_is_rejected(declared, fault):
    entry, _, model = declared
    if fault == "empty":
        model["base_instructions"] = ""
    elif fault == "boolean-window":
        model["context_window"] = True
    elif fault == "no-slug":
        model["slug"] = "\n"
    elif fault == "conflicting":
        model["model_messages"] = {"instructions_template": "Different instructions"}
    elif fault == "messages":
        model["model_messages"] = []
    models = [model, model] if fault == "ambiguous" else [model]
    changed = reference(Path(entry["path"]), json.dumps({"models": models}).encode())
    with pytest.raises(ValueError):
        catalogs.load_local_catalog(changed)


def test_modern_instruction_template_is_retained(declared):
    entry, _, model = declared
    template = model.pop("base_instructions")
    model["model_messages"] = {"instructions_template": template}
    local = catalogs.load_local_catalog(reference(Path(entry["path"]), json.dumps({"models": [model]}).encode()))
    assert local.metadata()["model_messages"]["instructions_template"] == template


@pytest.mark.parametrize(
    "provider", [None, {"base_url": "https://example.invalid/v1", "credential_env": "OWNED_FIXTURE"}]
)
def test_local_catalog_cannot_enter_another_authentication_mode(declared, provider):
    entry, context, _ = declared
    with pytest.raises(ValueError), catalogs.catalog_lease(context, provider, local=catalogs.load_local_catalog(entry)):
        pytest.fail("Local metadata entered an unqualified authentication mode")


def test_nested_or_mismatched_local_catalog_is_rejected(declared):
    entry, context, _ = declared
    local = catalogs.load_local_catalog(entry)
    with catalogs.catalog_lease(context, PROVIDER, local=local) as selected:
        with pytest.raises(ValueError, match="prior"), catalogs.catalog_lease(selected, PROVIDER, local=local):
            pytest.fail("Nested metadata lease was admitted")
        with pytest.raises(ValueError, match="requested model"):
            command(selected, "different-model", "high", provider=PROVIDER)
        with pytest.raises(ValueError):
            command(replace(selected, native_catalog=catalogs.NativeCatalog("{}")), MODEL, "high", provider=PROVIDER)


@pytest.mark.parametrize("path", ["relative.json", "C:\\owned\\..\\other.json", "\\\\server\\share\\catalog.json"])
def test_archived_catalog_cannot_change_its_path_domain(declared, path):
    record = catalogs.load_local_catalog(declared[0]).record()
    record["path"] = path
    with pytest.raises(ValueError):
        catalogs.decode_local_record(record)


def test_catalog_size_and_duplicate_fields_are_bounded(declared):
    entry, _, _ = declared
    for raw in (b"x" * (catalogs.LOCAL_CATALOG_LIMIT + 1), b'{"models": [], "models": []}'):
        with pytest.raises(ValueError):
            catalogs.load_local_catalog(reference(Path(entry["path"]), raw))


@pytest.mark.parametrize("fault", [None, "record", "command", "duplicate-command", "archive", "fallback"])
def test_native_boundary_checks_the_actual_catalog_launch_and_archive(declared, tmp_path, monkeypatch, fault):
    entry, _, _ = declared
    local = catalogs.load_local_catalog(entry)
    attempt = tmp_path / ".venv/attempt"
    (attempt / "inputs").mkdir(parents=True)
    launch: dict[str, Any] = {
        "context": {"local_catalog": local.record()},
        "command": ["owned-cli", "-c", "model_catalog_json=" + json.dumps(str(local.path()))],
    }
    if fault == "record":
        launch["context"]["local_catalog"]["sha256"] = "0" * 64
    elif fault == "command":
        launch["command"][-1] = 'model_catalog_json="different.json"'
    elif fault == "duplicate-command":
        launch["command"].extend(launch["command"][-2:])
    (attempt / "launch.json").write_text(json.dumps(launch), encoding="utf-8")
    (attempt / "inputs/model-catalog.json").write_bytes(local.content.encode() + (b" " if fault == "archive" else b""))
    event = {"type": "item.completed", "item": {"type": "error", "message": "Model metadata missing; fallback"}}
    (attempt / "transcript.jsonl").write_text(json.dumps(event) + "\n" if fault == "fallback" else "", encoding="utf-8")
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    inventory: dict[str, str] = {}
    if fault is not None:
        with pytest.raises(ValueError):
            boundary.local_catalog_control(attempt, local, inventory)
    else:
        boundary.local_catalog_control(attempt, local, inventory)
        assert inventory[str(attempt / "inputs/model-catalog.json")] == local.sha256
