"""Independent readiness and execution controls for the automatic environment."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import _bootstrap_doctor as doctor
import _bootstrap_launch as launch
import _native_shells as shells
import pytest


def distribution(name: str, version: str, requires: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(metadata={"Name": name}, version=version, requires=requires or [])


@pytest.fixture
def isolated_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "path", sys.path.copy())
    monkeypatch.setattr(sys, "argv", sys.argv.copy())


def test_doctor_checks_the_complete_dependency_graph(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_imports):
    lock = tmp_path / "requirements.txt"
    lock.write_text("alpha==1.0\nbeta==2.0\n", encoding="utf-8")
    installed = [distribution("Alpha", "1.0", ["beta>=2"]), distribution("beta", "2.0")]
    monkeypatch.setattr(doctor.importlib.metadata, "distributions", lambda **kwargs: installed)
    result = doctor.observation(tmp_path, [lock], ["json"])
    assert result["packages"] == [("alpha", "1.0"), ("beta", "2.0")]
    installed[0].requires = ["beta>=3"]
    with pytest.raises(ValueError, match="Unsatisfied installed dependency"):
        doctor.observation(tmp_path, [lock], [])


@pytest.mark.parametrize(
    ("locked", "installed", "message"),
    [
        ("alpha==1\n", [], "inventory differs"),
        ("alpha==1\n", [distribution("alpha", "1"), distribution("extra", "1")], "inventory differs"),
        ("alpha==1\n", [distribution("alpha", "1"), distribution("Alpha", "1")], "Duplicate installed"),
        ("alpha>=1\n", [distribution("alpha", "1")], "exact registry version pins"),
        ("alpha==1\nalpha==2\n", [distribution("alpha", "1")], "Conflicting locked"),
    ],
)
def test_doctor_refuses_incomplete_or_ambiguous_environments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, isolated_imports, locked, installed, message
):
    lock = tmp_path / "requirements.txt"
    lock.write_text(locked, encoding="utf-8")
    monkeypatch.setattr(doctor.importlib.metadata, "distributions", lambda **kwargs: installed)
    with pytest.raises(ValueError, match=message):
        doctor.observation(tmp_path, [lock], [])


def test_module_mode_imports_the_selected_checkout(tmp_path: Path, isolated_imports, capsys):
    name = "bootstrap_selected_checkout_probe"
    (tmp_path / (name + ".py")).write_text("import json,sys\nprint(json.dumps(sys.argv[1:]))\n", encoding="utf-8")
    assert launch.main(["--packages", str(tmp_path), "--root", str(tmp_path), "--", "-m", name, "", 'a"b', "λ"]) == 0
    assert json.loads(capsys.readouterr().out) == ["", 'a"b', "λ"]


def test_script_mode_does_not_execute_outside_the_selected_checkout(tmp_path: Path, isolated_imports):
    root = tmp_path / "checkout"
    root.mkdir()
    foreign = tmp_path / "foreign.py"
    foreign.write_text("raise AssertionError('must not run')\n", encoding="utf-8")
    with pytest.raises(ValueError, match="selected checkout"):
        launch.main(["--packages", str(root), "--root", str(root), "--", str(foreign)])


def test_declared_missing_shell_does_not_fall_back_to_host_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_SKILLS_BASH", str(tmp_path / "missing"))
    monkeypatch.setattr(shells.shutil, "which", lambda _: pytest.fail("Must not discover another host executable"))
    with pytest.raises(RuntimeError, match="declared GNU Bash"):
        shells.discover()


def test_declared_shell_preserves_its_logical_installation_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    suffix = ".exe" if shells.os.name == "nt" else ""
    for name in ("bash", "head", "wc", "dash"):
        (tmp_path / (name + suffix)).write_bytes(b"owned test fixture")
    bash = tmp_path / ("bash" + suffix)
    monkeypatch.setenv("AI_SKILLS_BASH", str(bash))
    monkeypatch.setenv("AI_SKILLS_UNIX_BIN", str(tmp_path))
    monkeypatch.setenv("AI_SKILLS_DASH", str(tmp_path / ("dash" + suffix)))
    monkeypatch.setattr(
        shells.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, b"GNU bash, version fixture\n"),
    )
    monkeypatch.setattr(Path, "resolve", lambda *args, **kwargs: pytest.fail("Must preserve the admitted logical path"))
    runtime = shells.discover()
    assert runtime is not None
    assert runtime.bash == bash.absolute()
    assert runtime.utilities == tmp_path.absolute()
