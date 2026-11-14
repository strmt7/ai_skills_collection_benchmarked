"""Native attempt admission must fail before subject launch or native grading."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import _native_trial_plan as plans
import pytest
from _native_benchmark_runtime import sha256


def ref(path: Path, data: bytes) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": str(path), "sha256": sha256(data)}


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    root = tmp_path / "controller"
    root.mkdir()
    monkeypatch.setattr(plans, "ROOT", root)
    monkeypatch.setattr(plans, "execution_sources", lambda: {"controller": "frozen"})
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    monkeypatch.setattr(plans, "subject_runtime", lambda entry: {"roots": (runtime_root,)})
    before = b"independent complete capture fixture"
    tree = tmp_path / "baseline-tree"
    tree.mkdir()
    monkeypatch.setattr(plans, "completed_capture", lambda *args: (before, tree))
    assets = tmp_path / "assets"
    task = {
        "collection_policy": {},
        "baseline_manifest_sha256": sha256(before),
        "verifier": ref(assets / "verifier", b"verifier"),
        "inventory": ref(assets / "inventory", b"cases"),
        "scorer": {"files": [], "wheels": []},
    }
    monkeypatch.setattr(plans, "validate_task", lambda value: value)
    plan = {
        "schema_version": 1,
        "id": "independent-development",
        "partition": "development",
        "condition": "default",
        "task": ref(assets / "task.json", json.dumps(task).encode()),
        "baseline_collection": str(tmp_path / "baseline"),
        "prompt": ref(assets / "prompt", b"Independent task brief."),
        "interventions": [],
        "model": "owned-local-fixture",
        "reasoning_effort": "high",
        "time_limit_seconds": 20,
        "provider": {"base_url": "http://127.0.0.1:8041/v1", "credential_env": "NATIVE_FIXTURE"},
        "subject_runtime": ref(assets / "subject.json", b"runtime"),
        "grader_runtime": ref(assets / "grader.json", b"grader"),
        "execution_source_sha256": {"controller": "frozen"},
    }
    path = tmp_path / "plan.json"
    return path, plan, runtime_root


def load(frozen):
    path, plan, _ = frozen
    path.write_text(json.dumps(plan), encoding="utf-8")
    return plans.load_plan(path)


def test_schema_three_admits_explicit_storage_and_write_budgets(frozen):
    limits = {"min_free_bytes": 1024**3, "max_workspace_bytes": 1024**2, "max_workspace_entries": 100}
    frozen[1].update(schema_version=3, write_io_limit_bytes=65536, storage_limits=limits)
    assert load(frozen)["plan"]["storage_limits"] == limits


@pytest.mark.parametrize(
    "limits",
    [None, {}, {"min_free_bytes": 1}, {"min_free_bytes": True, "max_workspace_bytes": 1, "max_workspace_entries": 1}],
)
def test_schema_three_rejects_incomplete_or_invalid_storage_limits(frozen, limits):
    frozen[1].update(schema_version=3, write_io_limit_bytes=65536, storage_limits=limits)
    with pytest.raises(ValueError):
        load(frozen)


@pytest.mark.parametrize("version", [1, 2])
def test_older_plans_cannot_silently_acquire_storage_guards(frozen, version):
    frozen[1].update(schema_version=version, storage_limits={})
    if version == 2:
        frozen[1]["write_io_limit_bytes"] = 65536
    with pytest.raises(ValueError, match="complete frozen"):
        load(frozen)


def test_default_attempt_preserves_its_frozen_brief_and_baseline(frozen):
    admitted = load(frozen)
    assert admitted["prompt"] == "Independent task brief."
    assert admitted["plan_sha256"] == sha256(frozen[0].read_bytes())
    assert admitted["before"] == b"independent complete capture fixture"


def test_schema_two_freezes_a_subject_write_budget(frozen):
    frozen[1].update(schema_version=2, write_io_limit_bytes=65536)
    assert load(frozen)["plan"]["write_io_limit_bytes"] == 65536


@pytest.mark.parametrize("limit", [None, False, 0, -1, 1.5, 1024**3 + 1])
def test_schema_two_rejects_invalid_subject_write_budgets(frozen, limit):
    frozen[1].update(schema_version=2, write_io_limit_bytes=limit)
    with pytest.raises(ValueError, match="budget"):
        load(frozen)


def test_legacy_plan_cannot_silently_add_an_undeclared_budget(frozen):
    frozen[1]["write_io_limit_bytes"] = 65536
    with pytest.raises(ValueError, match="complete frozen"):
        load(frozen)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("condition", ""),
        ("partition", "unknown"),
        ("time_limit_seconds", True),
        ("time_limit_seconds", 1801),
        ("reasoning_effort", "guess"),
        ("model", "\n"),
    ],
)
def test_invalid_attempt_declarations_are_rejected(frozen, field, value):
    frozen[1][field] = value
    with pytest.raises(ValueError):
        load(frozen)


def test_changed_controller_is_rejected_before_asset_access(frozen):
    frozen[1]["execution_source_sha256"] = {}
    with pytest.raises(ValueError, match="sources differ"):
        load(frozen)


def test_explicit_local_no_auth_provider_survives_frozen_plan_admission(frozen):
    declared = {"base_url": "http://127.0.0.1:8041/v1", "authentication": "none"}
    frozen[1]["provider"] = declared
    assert load(frozen)["plan"]["provider"] == declared


def test_default_condition_cannot_receive_collection_interventions(frozen):
    frozen[1]["interventions"] = [frozen[1]["prompt"]]
    with pytest.raises(ValueError, match="condition"):
        load(frozen)


def test_changed_prompt_is_rejected(frozen):
    Path(frozen[1]["prompt"]["path"]).write_bytes(b"different input")
    with pytest.raises(ValueError, match="frozen identity"):
        load(frozen)


def test_runtime_grant_cannot_expose_the_verifier(frozen):
    path, plan, runtime_root = frozen
    task = json.loads(Path(plan["task"]["path"]).read_bytes())
    task["verifier"] = ref(runtime_root / "hidden-verifier", b"verifier")
    plan["task"] = ref(Path(plan["task"]["path"]), json.dumps(task).encode())
    with pytest.raises(ValueError, match="expose"):
        load(frozen)


def test_intervention_assets_cannot_be_repeated_or_carry_extra_values(frozen):
    plan = frozen[1]
    plan["condition"] = "candidate"
    plan["interventions"] = [plan["prompt"], plan["prompt"]]
    with pytest.raises(ValueError, match="repeat"):
        load(frozen)
    plan["interventions"] = [{**plan["prompt"], "credential": "unselected fixture"}]
    with pytest.raises(ValueError, match="exactly"):
        load(frozen)


def test_evaluator_bytes_cannot_be_used_as_subject_instructions(frozen):
    plan = frozen[1]
    task = json.loads(Path(plan["task"]["path"]).read_bytes())
    plan["prompt"] = task["verifier"]
    with pytest.raises(ValueError, match="evaluator assets"):
        load(frozen)


def test_grader_wheel_bytes_cannot_be_used_as_subject_instructions(frozen):
    plan = frozen[1]
    path = Path(plan["task"]["path"])
    task = json.loads(path.read_bytes())
    task["python_environment"] = {"wheels": [plan["prompt"]]}
    plan["task"] = ref(path, json.dumps(task).encode())
    with pytest.raises(ValueError, match="evaluator assets"):
        load(frozen)


@pytest.mark.parametrize("mutation", [None, "missing", "changed", "extra", "directory", "python"])
@pytest.mark.parametrize(
    "schema,with_dependencies,with_catalog",
    [
        (1, False, False),
        (2, True, False),
        (3, False, True),
        (3, True, True),
        (4, False, False),
        (4, True, False),
        (4, False, True),
        (4, True, True),
    ],
)
def test_subject_runtime_checks_complete_cli_payload_and_python(
    tmp_path, monkeypatch, mutation, schema, with_dependencies, with_catalog
):
    root = tmp_path / "controller"
    pin_path = root / "toolchains/bootstrap/codex.json"
    package = tmp_path / "cli"
    executable = package / "package/vendor/bin/codex.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"admitted native fixture")
    python = tmp_path / "python.exe"
    python.write_bytes(b"admitted python fixture")
    pin = {
        "files": {
            "package/vendor/bin/codex.exe": {
                "bytes": executable.stat().st_size,
                "sha256": sha256(executable.read_bytes()),
            }
        },
        "resources": {name: ref(package / name, name.encode()) for name in ("LICENSE", "NOTICE")},
        "executable": "package/vendor/bin/codex.exe",
        "runtime_root": "package/vendor",
    }
    ref(pin_path, json.dumps(pin).encode())
    extra = {}
    if with_dependencies:
        extra = {
            "dependencies": ref(tmp_path / "dependency.json", b"owned specification fixture"),
            "installer": str(tmp_path / "uv.exe"),
            "archive_directory": None,
            "import_paths": ["src"],
        }
        monkeypatch.setattr(plans, "load_specification", lambda raw: {"admitted": True})
        monkeypatch.setattr(plans, "installer_identity", lambda path: {"admitted": True})
    if with_catalog:
        extra["model_catalog"] = ref(
            tmp_path / "model-catalog.json",
            json.dumps(
                {
                    "models": [
                        {
                            "slug": "owned-local",
                            "context_window": 65536,
                            "base_instructions": "Frozen native instructions.",
                        }
                    ]
                }
            ).encode(),
        )
    if schema == 4:
        native = tmp_path / "native-toolchain"
        native.mkdir()
        (native / "node.exe").write_bytes(b"native tool fixture")
        extra["toolchains"] = ref(
            tmp_path / "toolchains.json",
            json.dumps(
                {
                    "schema_version": 1,
                    "toolchains": [
                        {
                            "name": "node",
                            "version": "26.13.1",
                            "root": str(native),
                            "files": {
                                "node.exe": {
                                    "bytes": len(b"native tool fixture"),
                                    "sha256": sha256(b"native tool fixture"),
                                }
                            },
                            "directories": [],
                            "commands": {"node": ["node.exe"]},
                        }
                    ],
                }
            ).encode(),
        )
    runtime = ref(
        tmp_path / "runtime.json",
        json.dumps(
            {
                "schema_version": schema,
                "cli_package_root": str(package),
                "python": str(python),
                "python_sha256": sha256(python.read_bytes()),
                **extra,
            }
        ).encode(),
    )
    monkeypatch.setattr(plans, "ROOT", root)
    if mutation == "missing":
        executable.unlink()
    elif mutation == "changed":
        executable.write_bytes(b"x" * executable.stat().st_size)
    elif mutation == "extra":
        (executable.parent / "undeclared.exe").write_bytes(b"unadmitted fixture")
    elif mutation == "directory":
        (executable.parent / "undeclared-directory").mkdir()
    elif mutation == "python":
        python.write_bytes(b"different interpreter fixture")
    if mutation is None:
        admitted = plans.subject_runtime(runtime)
        assert admitted["cli"] == executable and admitted["python"] == python
        if with_catalog:
            assert admitted["local_catalog"].metadata()["slug"] == "owned-local"
        if schema == 4:
            assert admitted["toolchains"].roots() == (native,)
            assert native in admitted["roots"]
            plan: dict[str, Any] = {key: runtime for key in ("task", "subject_runtime", "grader_runtime", "prompt")}
            plan["interventions"] = []
            assert plans.input_assets(plan, admitted)["native-toolchains.json"] == extra["toolchains"]
    else:
        with pytest.raises(ValueError):
            plans.subject_runtime(runtime)


@pytest.mark.parametrize("fault", [None, "model", "authentication", "runtime-grant", "evaluator"])
def test_local_metadata_is_bound_to_the_task_and_kept_outside_subject_grants(frozen, monkeypatch, fault):
    path, plan, runtime_root = frozen
    location = (runtime_root if fault == "runtime-grant" else path.parent) / "local-catalog.json"
    entry = ref(
        location,
        json.dumps(
            {
                "models": [
                    {"slug": plan["model"], "context_window": 65536, "base_instructions": "Frozen native instructions."}
                ]
            }
        ).encode(),
    )
    local = plans.load_local_catalog(entry)
    runtime = {"roots": (runtime_root,), "local_catalog": local}
    monkeypatch.setattr(plans, "subject_runtime", lambda entry: runtime)
    if fault != "authentication":
        plan["provider"] = {"authentication": "none", "base_url": "http://127.0.0.1:8123/v1"}
    if fault == "model":
        plan["model"] = "different-model"
    if fault == "evaluator":
        task_path = Path(plan["task"]["path"])
        task = json.loads(task_path.read_bytes())
        task["verifier"] = entry
        plan["task"] = ref(task_path, json.dumps(task).encode())
    if fault is not None:
        with pytest.raises(ValueError):
            load(frozen)
    else:
        assert load(frozen)["runtime"]["local_catalog"] is local
        assert plans.input_assets(plan, runtime)["model-catalog.json"] == entry


def test_source_archive_matches_the_frozen_implementation(tmp_path, monkeypatch):
    root = tmp_path / "controller"
    root.mkdir()
    data = b"independent source fixture\n"
    (root / "source.py").write_bytes(data)
    expected = {"source.py": sha256(data)}
    monkeypatch.setattr(plans, "ROOT", root)
    monkeypatch.setattr(plans, "execution_sources", lambda: expected)
    output = tmp_path / "archive"
    plans.archive_sources(output, expected)
    assert (output / "source.py").read_bytes() == data
    (root / "source.py").write_bytes(b"changed source")
    with pytest.raises(ValueError, match="during archival"):
        plans.archive_sources(tmp_path / "changed-archive", expected)


def test_native_toolchain_manifest_cannot_be_inside_a_subject_read_grant(frozen, monkeypatch):
    _, _, runtime_root = frozen
    manifest = runtime_root / "toolchains.json"
    manifest.write_bytes(b"frozen declaration")
    runtime = {"roots": (runtime_root,), "toolchains": SimpleNamespace(location=str(manifest))}
    monkeypatch.setattr(plans, "subject_runtime", lambda entry: runtime)
    with pytest.raises(ValueError, match="controller or evaluator"):
        load(frozen)
