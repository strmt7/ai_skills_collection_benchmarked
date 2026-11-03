"""Exercise the lock verifier against real uv and a synthetic offline wheel index."""

from __future__ import annotations

import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import pytest
import verify_dev_lock as module


@pytest.fixture
def uv() -> str:
    path = os.environ.get("AI_SKILLS_TEST_UV") or shutil.which("uv")
    if path is None:
        if os.environ.get("AI_SKILLS_REQUIRE_UV") == "1":
            pytest.fail("uv 0.13.6 is required")
        pytest.skip("uv 0.13.6 is required for the offline integration controls")
    result = subprocess.run([path, "--version"], capture_output=True, text=True, check=False, timeout=30)
    if result.returncode or result.stdout.split()[:2] != ["uv", "0.13.6"]:
        if os.environ.get("AI_SKILLS_REQUIRE_UV") == "1":
            pytest.fail("uv 0.13.6 is required")
        pytest.skip("uv 0.13.6 is required for the offline integration controls")
    return str(Path(path).resolve())


def wheel(directory: Path, name: str, version: str) -> None:
    normalized = name.replace("-", "_")
    dist = f"{normalized}-{version}.dist-info"
    with zipfile.ZipFile(directory / f"{normalized}-{version}-py3-none-any.whl", "w") as archive:
        archive.writestr(f"{normalized}/__init__.py", "")
        archive.writestr(
            f"{dist}/METADATA", f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\nRequires-Python: >=3.11\n"
        )
        archive.writestr(f"{dist}/WHEEL", "Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
        archive.writestr(f"{dist}/RECORD", "")


@pytest.fixture
def fixture(tmp_path: Path, uv: str) -> tuple[Path, Path, str, tuple[str, ...]]:
    wheels = tmp_path / "wheels"
    wheels.mkdir()
    for name in ("demo-package", "demo-builder"):
        for version in ("1.0", "2.0"):
            wheel(wheels, name, version)
    project = tmp_path / "pyproject.toml"
    project.write_text(
        '[project]\nname = "local-lock-fixture"\nversion = "1.0"\nrequires-python = ">=3.11"\n'
        'dependencies = ["demo-package==1.0"]\n\n'
        "[project.optional-dependencies]\ntest = []\nlint = []\n\n"
        '[build-system]\nrequires = ["demo-builder==1.0"]\nbuild-backend = "unused"\n',
        encoding="utf-8",
        newline="\n",
    )
    build = tmp_path / "build.in"
    build.write_text("demo-builder==1.0\n", encoding="utf-8", newline="\n")
    lock = tmp_path / "dev.lock"
    source = ("--no-index", "--find-links", str(wheels))
    args = [
        uv,
        "pip",
        "compile",
        str(project),
        str(build),
        "--extra",
        "test",
        "--extra",
        "lint",
        "--universal",
        "--python-version",
        "3.11.18",
        "--generate-hashes",
        "--no-strip-markers",
        "--only-binary=:all:",
        "--no-annotate",
        "--no-header",
        "--no-config",
        *source,
        "--output-file",
        str(lock),
        "--quiet",
    ]
    subprocess.run(args, check=True, capture_output=True, timeout=60)
    return project, lock, uv, source


def test_valid_lock(fixture: tuple[Path, Path, str, tuple[str, ...]]) -> None:
    assert module.verify(*fixture)["valid"] is True


@pytest.mark.parametrize("target", ["runtime", "build", "hash"])
def test_stale_or_corrupted_lock_is_rejected(fixture: tuple[Path, Path, str, tuple[str, ...]], target: str) -> None:
    project, lock, uv, source = fixture
    if target in {"runtime", "build"}:
        text = project.read_text(encoding="utf-8")
        old = "demo-package==1.0" if target == "runtime" else "demo-builder==1.0"
        assert text.count(old) == 1
        project.write_text(text.replace(old, old.replace("1.0", "2.0")), encoding="utf-8", newline="\n")
    else:
        text = lock.read_text(encoding="utf-8")
        index = text.index("sha256:") + len("sha256:")
        changed = "0" if text[index] != "0" else "1"
        lock.write_text(text[:index] + changed + text[index + 1 :], encoding="utf-8", newline="\n")
    assert module.verify(project, lock, uv, source)["valid"] is False


@pytest.mark.parametrize("target", ["project", "lock"])
def test_concurrent_input_change_is_rejected(
    fixture: tuple[Path, Path, str, tuple[str, ...]], monkeypatch: pytest.MonkeyPatch, target: str
) -> None:
    project, lock, uv, source = fixture
    original = module.subprocess.run
    changed = project if target == "project" else lock

    def hooked(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        result = original(*args, **kwargs)
        if args and isinstance(args[0], list) and args[0][1:3] == ["pip", "compile"]:
            with changed.open("a", encoding="utf-8", newline="\n") as output:
                output.write("\n# changed during verification\n")
        return result

    monkeypatch.setattr(module.subprocess, "run", hooked)
    with pytest.raises(ValueError, match="changed during verification"):
        module.verify(project, lock, uv, source)


@pytest.mark.parametrize("change", ["dynamic", "custom-uv", "inline-hash"])
def test_unsupported_inputs_are_rejected(fixture: tuple[Path, Path, str, tuple[str, ...]], change: str) -> None:
    project, lock, uv, source = fixture
    if change == "dynamic":
        text = project.read_text(encoding="utf-8").replace("[project]\n", '[project]\ndynamic = ["description"]\n')
        project.write_text(text, encoding="utf-8")
    elif change == "custom-uv":
        with project.open("a", encoding="utf-8") as output:
            output.write("\n[tool.uv]\nprerelease = 'allow'\n")
    else:
        text = lock.read_text(encoding="utf-8").replace(" \\\n    --hash=", " --hash=", 1)
        lock.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        module.verify(project, lock, uv, source)
