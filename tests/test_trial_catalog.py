from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import _trial_catalog as catalog
import pytest
from _trial_context import TrialContext, command
from _trial_signin import NativeSignin


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    cli = runtime / "bin/codex.exe"
    cli.parent.mkdir()
    cli.write_bytes(b"owned-native-executable")
    model_data = b'{"models": []}\n'
    model_path = runtime / "models.json"
    model_path.write_bytes(model_data)
    source = "c" * 40
    pin = {
        "executable": "bin/codex.exe",
        "source_commit": source,
        "files": {
            "bin/codex.exe": {"bytes": cli.stat().st_size, "sha256": hashlib.sha256(cli.read_bytes()).hexdigest()}
        },
        "resources": {
            "models.json": {
                "bytes": len(model_data),
                "sha256": hashlib.sha256(model_data).hexdigest(),
                "url": f"https://raw.githubusercontent.com/openai/codex/{source}/codex-rs/models-manager/models.json",
            }
        },
    }
    pin_path = tmp_path / "pin.json"
    pin_path.write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(catalog, "PIN", pin_path)
    monkeypatch.setattr(catalog, "checked_path", lambda path: path.resolve())
    auth, home, workspace = (tmp_path / name for name in ("auth", "controller", "workspace"))
    for path in (auth, home, workspace):
        path.mkdir()
    context = TrialContext(
        home,
        workspace,
        cli,
        runtime / "python.exe",
        (runtime,),
        {"CODEX_HOME": str(auth)},
        {},
        NativeSignin(auth, "file", {}),
    )
    provider = {"authentication": "codex_signin", "codex_home": str(auth), "credential_store": "file"}
    return context, provider, pin_path, model_path


def test_native_catalog_lease_uses_public_pin_and_preserves_original_context(admitted):
    context, provider, pin_path, model_path = admitted
    original_environment = context.controller_environment.copy()
    with catalog.catalog_lease(context, provider) as selected:
        assert selected is not context and context.native_catalog is None
        assert selected.native_catalog is not None
        assert selected.native_catalog.source_sha256 == hashlib.sha256(pin_path.read_bytes()).hexdigest()
        assert selected.native_catalog.path(selected.cli) == model_path
        invocation = command(selected, "gpt-6.1-sol", "high", provider=provider)
        assert "model_catalog_json=" + json.dumps(str(model_path)) in invocation
        assert "--ignore-user-config" in invocation
    assert context.controller_environment == original_environment


@pytest.mark.parametrize("resource", ["catalog", "cli"])
@pytest.mark.parametrize("fault", ["missing", "same-size-content", "growth"])
def test_changed_native_inputs_are_rejected_before_lease(admitted, resource, fault):
    context, provider, _, model_path = admitted
    path = model_path if resource == "catalog" else context.cli
    if fault == "missing":
        path.unlink()
    else:
        raw = path.read_bytes()
        path.write_bytes(b"x" * len(raw) if fault == "same-size-content" else raw + b"x")
    with pytest.raises(ValueError), catalog.catalog_lease(context, provider):
        pytest.fail("Changed native inputs entered the lease")


@pytest.mark.parametrize("resource", ["catalog", "cli"])
def test_inputs_changed_during_subject_execution_fail_on_scope_exit(admitted, resource):
    context, provider, _, model_path = admitted
    with pytest.raises(ValueError), catalog.catalog_lease(context, provider):
        path = model_path if resource == "catalog" else context.cli
        path.write_bytes(path.read_bytes() + b"x")


def test_ordinary_subject_failure_is_preserved_when_catalog_is_unchanged(admitted):
    context, provider, _, _ = admitted
    with pytest.raises(RuntimeError, match="owned subject failure"), catalog.catalog_lease(context, provider):
        raise RuntimeError("owned subject failure")


@pytest.mark.parametrize("provider", [None, {"authentication": "none", "base_url": "http://127.0.0.1:8123/v1"}])
def test_non_native_catalog_lease_neither_loads_pin_nor_changes_context(admitted, provider):
    context, _, pin_path, _ = admitted
    pin_path.unlink()
    context = replace(context, signin=None)
    with catalog.catalog_lease(context, provider) as selected:
        assert selected is context


def test_native_lease_requires_admitted_signin_and_prevents_nested_catalog_binding(admitted):
    context, provider, _, _ = admitted
    with (
        pytest.raises(ValueError, match="admitted native sign-in"),
        catalog.catalog_lease(replace(context, signin=None), provider),
    ):
        pytest.fail("Missing native admission was accepted")
    with (
        catalog.catalog_lease(context, provider) as selected,
        pytest.raises(ValueError, match="prior catalog"),
        catalog.catalog_lease(selected, provider),
    ):
        pytest.fail("Nested catalog binding was accepted")


def test_signed_in_command_without_catalog_binding_is_never_constructed(admitted):
    context, provider, _, _ = admitted
    with pytest.raises(ValueError):
        command(context, "gpt-6.1-sol", "high", provider=provider)


def test_catalog_record_reconstructs_commands_without_original_host_files(admitted):
    context, provider, _, model_path = admitted
    with catalog.catalog_lease(context, provider) as selected:
        assert selected.native_catalog is not None
        record = selected.native_catalog.record()
    original = catalog.decode_record(record, context.cli)
    model_path.unlink()
    context.cli.unlink()
    replayed = catalog.decode_record(record, context.cli)
    assert original == replayed and replayed.path(context.cli) == model_path


@pytest.mark.parametrize(
    "value", [None, [], {}, {"pin": 1}, {"pin": "{}", "extra": True}, {"pin": "x" * (128 * 1024 + 1)}, {"pin": "null"}]
)
def test_record_shape_and_size_are_not_inferred_from_omission(admitted, value):
    context, _, _, _ = admitted
    with pytest.raises(ValueError):
        catalog.decode_record(value, context.cli)


@pytest.mark.parametrize(
    "fault", ["parent", "absolute", "source", "sha256", "size", "boolean-size", "missing-resource"]
)
def test_pinned_catalog_cannot_redirect_source_or_package_layout(admitted, fault):
    context, _, pin_path, _ = admitted
    pin = json.loads(pin_path.read_bytes())
    if fault == "parent":
        pin["executable"] = "../bin/codex.exe"
    elif fault == "absolute":
        pin["executable"] = "/bin/codex.exe"
    elif fault == "missing-resource":
        pin["resources"].clear()
    else:
        key, value = {
            "source": ("url", "https://example.invalid/models.json"),
            "sha256": ("sha256", "invalid"),
            "size": ("bytes", 2 * 1024**2 + 1),
            "boolean-size": ("bytes", True),
        }[fault]
        pin["resources"]["models.json"][key] = value
    with pytest.raises(ValueError):
        catalog.decode_record({"pin": json.dumps(pin)}, context.cli)


def test_catalog_rejects_a_cli_location_outside_its_declared_layout(admitted):
    context, _, pin_path, _ = admitted
    with pytest.raises(ValueError, match="package layout"):
        catalog.decode_record({"pin": pin_path.read_text()}, context.cli.parent / "other.exe")
