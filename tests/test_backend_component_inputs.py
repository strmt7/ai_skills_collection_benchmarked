"""Check that the backend benchmark binds the sources its controls consume."""

import hashlib
import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTROLS = Path("benchmarks/component-controls/backend")
PACKAGES = Path("included/improved/skills")
PREPARE = CONTROLS / "prepare_backend.py"


def test_backend_bindings_follow_the_executed_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    spec = importlib.util.spec_from_file_location("backend_component_prepare", ROOT / PREPARE)
    assert spec is not None and spec.loader is not None
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    original, bindings = prepare.modules()
    guidance = PACKAGES / "backend-patterns-current/SKILL.md"
    executable = PACKAGES / "backend-patterns-current/references/boundaries.ts"
    assert bindings[executable.as_posix()] == hashlib.sha256((ROOT / executable).read_bytes()).hexdigest()
    assert guidance.as_posix() not in bindings

    for name in [*map(Path, bindings), guidance]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    monkeypatch.setattr(prepare, "ROOT", tmp_path)
    monkeypatch.setattr(prepare, "HERE", tmp_path / CONTROLS)
    monkeypatch.setattr(prepare, "PACKAGES", tmp_path / PACKAGES)

    with (tmp_path / guidance).open("a", encoding="utf-8") as stream:
        stream.write("\nReview the worker's acknowledgement boundary.\n")
    assert prepare.modules() == (original, bindings)

    changed = original["boundaries.mts"] + "\nexport const sourceBindingProbe = 1;\n"
    (tmp_path / executable).write_text(changed, encoding="utf-8", newline="\n")
    programs, updated = prepare.modules()
    assert programs == {**original, "boundaries.mts": changed}
    assert updated == {**bindings, executable.as_posix(): hashlib.sha256(changed.encode("utf-8")).hexdigest()}
