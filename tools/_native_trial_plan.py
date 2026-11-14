"""Admit a frozen native benchmark attempt without importing subject instructions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import sha256
from _trial_catalog import load_local_catalog
from _trial_provider import validate_provider
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_storage_budget import StorageLimits
from grade_swe_skills_submission import asset, completed_capture, source_hashes, validate_task
from prepare_subject_dependencies import installer_identity, load_specification

ROOT = Path(__file__).resolve().parents[1]


def execution_sources() -> dict[str, str]:
    """Bind runtime and grader sources; boundary receipts separately bind admission code."""
    names = (
        "tools/_native_trial_plan.py",
        "tools/run_swe_skills_trial.py",
        "toolchains/bootstrap/codex.json",
        "tools/prepare_subject_dependencies.py",
        "tools/_bootstrap_doctor.py",
        "tools/appcontainer_dependencies.py",
        "toolchains/bootstrap/manifest.json",
    )
    return {**source_hashes(), **{name: sha256((ROOT / name).read_bytes()) for name in names}}


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value) is not None


def subject_runtime(entry: Any) -> dict[str, Any]:
    """Verify the complete CLI payload and explicit Python executable identity."""
    runtime = strict_json(asset(entry).decode("utf-8"))
    basic = {"schema_version", "cli_package_root", "python", "python_sha256"}
    extra = {"dependencies", "installer", "archive_directory", "import_paths"}
    if (
        not isinstance(runtime, dict)
        or type(runtime["schema_version"]) is not int
        or (runtime["schema_version"], set(runtime))
        not in ((1, basic), (2, basic | extra), (3, basic | {"model_catalog"}), (3, basic | extra | {"model_catalog"}))
    ):
        raise ValueError("Expected an explicit subject runtime declaration")
    package, python = (checked_path(Path(runtime[name])) for name in ("cli_package_root", "python"))
    pin = strict_json((ROOT / "toolchains/bootstrap/codex.json").read_text(encoding="utf-8"))
    pending = [package / "package"]
    directories = {parent.as_posix() for name in pin["files"] for parent in Path(name).parents if str(parent) != "."}
    seen: set[str] = set()
    visited = 0
    while pending:
        visited += 1
        if visited > 512:
            raise ValueError("Subject CLI directory inventory exceeds its admission budget")
        for path in checked_path(pending.pop()).iterdir():
            checked_path(path)
            if path.is_dir():
                if path.relative_to(package).as_posix() not in directories:
                    raise ValueError("Subject CLI package contains an undeclared directory")
                pending.append(path)
            elif path.is_file():
                name = path.relative_to(package).as_posix()
                if name not in pin["files"]:
                    raise ValueError("Subject CLI package contains an undeclared file")
                seen.add(name)
            else:
                raise ValueError("Subject CLI package contains an unsupported object")
    if seen != set(pin["files"]):
        raise ValueError("Subject CLI package is missing declared files")
    for name, identity in pin["files"].items():
        path = checked_path(package / name)
        if not path.is_relative_to(package) or path.stat().st_size != identity["bytes"]:
            raise ValueError("Subject CLI payload differs from the admitted package")
        if sha256(path.read_bytes()) != identity["sha256"]:
            raise ValueError("Subject CLI payload differs from the admitted package")
    for name, identity in pin["resources"].items():
        asset({"path": str(package / name), "sha256": identity["sha256"]})
    if not isinstance(runtime["python_sha256"], str) or sha256(python.read_bytes()) != runtime["python_sha256"]:
        raise ValueError("Subject Python differs from its frozen runtime identity")
    dependencies = {}
    if "dependencies" in runtime:
        entry = runtime["dependencies"]
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("Subject dependencies require a frozen specification asset")
        raw = asset(entry)
        load_specification(raw)
        installer = checked_path(Path(runtime["installer"]))
        installer_identity(installer)
        paths = runtime["import_paths"]
        if (
            not isinstance(paths, list)
            or len(paths) > 16
            or any(
                not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*", name)
                for name in paths
            )
            or len(set(paths)) != len(paths)
        ):
            raise ValueError("Subject import paths require unique safe workspace-relative directories")
        archives = runtime["archive_directory"]
        if archives is not None:
            archives = checked_path(Path(archives))
            if not archives.is_dir():
                raise ValueError("Subject dependency archives must name an existing directory")
        dependencies = {
            "dependencies": {
                "asset": entry,
                "raw": raw,
                "installer": installer,
                "archive_dir": archives,
                "import_paths": paths,
            }
        }
    return {
        "cli": package / pin["executable"],
        "python": python,
        "roots": (package / pin["runtime_root"], python.parent),
        **dependencies,
        **({"local_catalog": load_local_catalog(runtime["model_catalog"])} if runtime["schema_version"] == 3 else {}),
    }


def input_assets(plan: dict[str, Any], runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    """Name frozen inputs independently of their source filenames."""
    return {
        **{name + ".json": plan[name] for name in ("task", "subject_runtime", "grader_runtime")},
        "prompt.txt": plan["prompt"],
        **{f"interventions/{index:04d}.txt": entry for index, entry in enumerate(plan["interventions"])},
        **({"model-catalog.json": runtime["local_catalog"].asset()} if runtime and "local_catalog" in runtime else {}),
    }


def archive_sources(output: Path, expected: dict[str, str]) -> None:
    """Retain the exact implementation bytes behind this attempt's source identities."""
    if expected != execution_sources():
        raise ValueError("Native attempt sources changed before archival")
    output.mkdir(exist_ok=False)
    for name, identity in expected.items():
        data = (ROOT / name).read_bytes()
        if sha256(data) != identity:
            raise ValueError("Native attempt source changed during archival")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)


def load_plan(path: Path) -> dict[str, Any]:
    """Admit all declared bytes before a subject process or grader container starts."""
    path = checked_path(path)
    if path.stat().st_size > 16 * 1024**2:
        raise ValueError("Native attempt plan exceeds the input budget")
    raw = path.read_bytes()
    plan = strict_json(raw.decode("utf-8"))
    fields = {
        "schema_version",
        "id",
        "partition",
        "condition",
        "task",
        "baseline_collection",
        "prompt",
        "interventions",
        "model",
        "reasoning_effort",
        "time_limit_seconds",
        "provider",
        "subject_runtime",
        "grader_runtime",
        "execution_source_sha256",
    }
    if isinstance(plan, dict) and plan.get("schema_version") in (2, 3):
        fields.add("write_io_limit_bytes")
    if isinstance(plan, dict) and plan.get("schema_version") == 3:
        fields.add("storage_limits")
    if (
        not isinstance(plan, dict)
        or set(plan) != fields
        or type(plan["schema_version"]) is not int
        or plan["schema_version"] not in (1, 2, 3)
    ):
        raise ValueError("Expected a complete frozen native attempt plan")
    if plan["execution_source_sha256"] != execution_sources():
        raise ValueError("Native attempt sources differ from the frozen plan")
    if (
        not _identifier(plan["id"])
        or not _identifier(plan["condition"])
        or plan["partition"] not in ("development", "holdout")
        or not isinstance(plan["model"], str)
        or not plan["model"].strip()
        or any(ord(char) < 32 for char in plan["model"])
        or plan["reasoning_effort"] not in ("low", "medium", "high", "xhigh", "max")
        or type(plan["time_limit_seconds"]) is not int
        or not 1 <= plan["time_limit_seconds"] <= 1800
        or not isinstance(plan["interventions"], list)
        or len(plan["interventions"]) > 32
        or (plan["condition"] == "default" and plan["interventions"])
        or (
            plan["schema_version"] in (2, 3)
            and (type(plan["write_io_limit_bytes"]) is not int or not 0 < plan["write_io_limit_bytes"] <= 1024**3)
        )
    ):
        raise ValueError("Native attempt identity, condition or execution budget is invalid")
    if plan["schema_version"] == 3:
        StorageLimits.from_record(plan["storage_limits"])
    validate_provider(plan["provider"])
    references = list(input_assets(plan).values())
    if any(not isinstance(entry, dict) or set(entry) != {"path", "sha256"} for entry in references):
        raise ValueError("Native plan assets require exactly path and sha256")
    names = [str(Path(entry["path"]).resolve()).casefold() for entry in plan["interventions"]]
    if len(set(names)) != len(names):
        raise ValueError("A native condition must not repeat an intervention")
    task = validate_task(strict_json(asset(plan["task"]).decode("utf-8")))
    grader_assets = [task["verifier"], task["inventory"], *task["scorer"]["files"], *task["scorer"]["wheels"]]
    grader_assets.extend(task.get("python_environment", {}).get("wheels", []))
    grader_hashes = {entry["sha256"] for entry in grader_assets}
    if any(entry["sha256"] in grader_hashes for entry in [plan["prompt"], *plan["interventions"]]):
        raise ValueError("Subject instructions must not expose native evaluator assets")
    baseline = checked_path(Path(plan["baseline_collection"]))
    before, tree = completed_capture(baseline, task["collection_policy"])
    if sha256(before) != task["baseline_manifest_sha256"]:
        raise ValueError("Native attempt baseline differs from its frozen task")
    prompt = asset(plan["prompt"]).decode("utf-8")
    if not prompt.strip():
        raise ValueError("A native attempt requires a substantive frozen prompt")
    interventions = [asset(entry).decode("utf-8") for entry in plan["interventions"]]
    if any(not text.strip() for text in interventions):
        raise ValueError("A native intervention cannot be empty")
    if sum(len(text.encode("utf-8")) for text in [prompt, *interventions]) > 1024**2:
        raise ValueError("Native attempt prompt exceeds the one-MiB input budget")
    runtime = subject_runtime(plan["subject_runtime"])
    if "local_catalog" in runtime:
        catalog = runtime["local_catalog"]
        if validate_provider(plan["provider"]).get("authentication") != "none":
            raise ValueError("Local model metadata requires an anonymous provider")
        if catalog.metadata()["slug"] != plan["model"]:
            raise ValueError("Local catalog differs from the requested model")
        if catalog.sha256 in grader_hashes:
            raise ValueError("Model metadata must not expose native evaluator assets")
    asset(plan["grader_runtime"])
    protected = [
        path,
        baseline,
        tree,
        *(Path(plan[name]["path"]) for name in ("task", "prompt", "subject_runtime", "grader_runtime")),
    ]
    protected.extend(Path(entry["path"]) for entry in plan["interventions"])
    protected.extend(ROOT / name for name in execution_sources())
    if "dependencies" in runtime:
        protected.append(Path(runtime["dependencies"]["asset"]["path"]))
    if "local_catalog" in runtime:
        protected.append(Path(runtime["local_catalog"].location))
    protected.extend(Path(task[name]["path"]) for name in ("verifier", "inventory"))
    protected.extend(Path(entry["path"]) for entry in [*task["scorer"]["files"], *task["scorer"]["wheels"]])
    protected.extend(Path(entry["path"]) for entry in task.get("python_environment", {}).get("wheels", []))
    for root in runtime["roots"]:
        if ROOT.is_relative_to(root) or any(item.resolve().is_relative_to(root) for item in protected):
            raise ValueError("Subject runtime grants would expose controller or evaluator inputs")
    return {
        "plan": plan,
        "plan_raw": raw,
        "plan_sha256": sha256(raw),
        "task": task,
        "baseline": baseline,
        "before": before,
        "tree": tree,
        "runtime": runtime,
        "prompt": "\n\n".join([prompt, *interventions]),
        "grader_runtime": Path(plan["grader_runtime"]["path"]),
    }
