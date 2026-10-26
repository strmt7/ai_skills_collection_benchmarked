"""Independent controls for the maintained poster-preflight overlay."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from audit_skill_quality import missing_markdown_links

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "included/skills/by-category/science-research-data-analysis/latest-release-community/latex-posters"
OVERLAY = (
    ROOT / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/latex-posters"
)
SCRIPT = OVERLAY / "scripts/review_poster.sh"


def canonical(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def bash_and_path() -> tuple[str, str]:
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            home = Path(git).resolve().parent.parent
            candidate = home / "bin/bash.exe"
            if candidate.is_file():
                return str(candidate), str(home / "usr/bin")
        pytest.skip("Git Bash is not available")
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("Bash is not available")
    return bash, os.defpath


@pytest.fixture
def controls(tmp_path: Path) -> tuple[Path, str, dict[str, str]]:
    bash, utilities = bash_and_path()
    spies = tmp_path / "inspectors"
    spies.mkdir()
    scripts = {
        "pdfinfo": """#!/bin/bash
if [ "$CONTROL" = fail ]; then echo 'inspector failed' >&2; exit 7; fi
if [ "$CONTROL" = malformed ]; then echo 'bad output'; exit 0; fi
if [ "$CONTROL" = warn ]; then echo 'nonfatal warning' >&2; fi
if [ "$CONTROL" = multipage ]; then pages=2; else pages=1; fi
printf 'Pages: %s\\nPage size: 841.89 x 1190.55 pts\\n' "$pages"
if [ "$CONTROL" = duplicate ]; then echo 'Pages: 1'; fi
""",
        "pdffonts": """#!/bin/bash
if [ "$CONTROL" = warn ]; then echo 'nonfatal warning' >&2; fi
printf 'name type encoding emb sub uni object ID\\n'
if [ "$CONTROL" = badfont ]; then echo 'not-a-separator'; else echo '---- ---- -------- --- --- --- ---------'; fi
if [ "$CONTROL" = unembedded ]; then printf 'Example Type1 WinAnsi no no no 1 0\\n'; fi
""",
        "pdfimages": """#!/bin/bash
if [ "$CONTROL" = warn ]; then echo 'nonfatal warning' >&2; fi
printf 'page num type width height color comp bpc enc interp object ID x-ppi y-ppi size ratio\\n'
if [ "$CONTROL" = badimage ]; then echo 'not-a-separator'; else echo '----'; fi
if [ "$CONTROL" = lowppi ]; then printf '1 0 image 120 120 rgb 3 8 image no 1 0 100 100 20B 1%%\\n'; fi
if [ "$CONTROL" = unknown ]; then printf '1 0 unknown 120 120 rgb 3 8 image no 1 0 300 300 20B 1%%\\n'; fi
""",
    }
    for name, script in scripts.items():
        path = spies / name
        path.write_text(script, encoding="utf-8", newline="\n")
        path.chmod(0o755)
    (tmp_path / "-poster.pdf").write_bytes(b"owned fixture")
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join((str(spies), utilities))
    env["LC_ALL"] = "C"
    return tmp_path, bash, env


def run_preflight(controls: tuple[Path, str, dict[str, str]], scenario: str) -> subprocess.CompletedProcess[str]:
    directory, bash, env = controls
    env = {**env, "CONTROL": scenario}
    return subprocess.run(
        [bash, "--noprofile", "--norc", str(SCRIPT), "-poster.pdf"],
        cwd=directory,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )


@pytest.mark.parametrize(
    ("scenario", "exit_code", "message"),
    [
        ("normal", 0, "13 bytes"),
        ("warn", 0, "Automated preflight passed"),
        ("multipage", 1, "Expected one page"),
        ("fail", 1, "pdfinfo could not inspect"),
        ("malformed", 1, "Expected one page"),
        ("duplicate", 1, "Expected one page"),
        ("badfont", 1, "Unrecognized font report"),
        ("badimage", 1, "Unrecognized image report"),
        ("unembedded", 1, "not embedded"),
        ("lowppi", 0, "below 300 PPI"),
        ("unknown", 1, "Unrecognized image report"),
    ],
)
def test_independent_controls(
    controls: tuple[Path, str, dict[str, str]], scenario: str, exit_code: int, message: str
) -> None:
    result = run_preflight(controls, scenario)
    assert result.returncode == exit_code
    assert message in result.stdout
    if scenario == "unembedded":
        assert "Unembedded font: Example" in result.stdout
    if scenario == "lowppi":
        assert "Low-resolution image:" in result.stdout
    if scenario in {"warn", "fail"}:
        assert "warning" in result.stderr or "inspector failed" in result.stderr


def test_missing_inspectors_and_invalid_arguments(controls: tuple[Path, str, dict[str, str]]) -> None:
    directory, bash, env = controls
    isolated = directory / "only-wc"
    isolated.mkdir()
    wc = isolated / "wc"
    wc.write_text("#!/bin/bash\nprintf '13\\n'\n", encoding="utf-8", newline="\n")
    wc.chmod(0o755)
    env = {**env, "PATH": str(isolated)}
    result = subprocess.run(
        [bash, "--noprofile", "--norc", str(SCRIPT), "-poster.pdf"],
        cwd=directory,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    assert "incomplete" in result.stdout
    missing = subprocess.run(
        [bash, "--noprofile", "--norc", str(SCRIPT), "missing.pdf"],
        cwd=directory,
        env=env,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert missing.returncode == 1


@pytest.mark.skipif(os.name != "nt", reason="native Windows paths require Windows")
def test_native_windows_absolute_unicode_path(controls: tuple[Path, str, dict[str, str]]) -> None:
    directory, bash, env = controls
    fixture = directory / "-poster \u00f6 123.pdf"
    fixture.write_bytes(b"owned fixture")
    result = subprocess.run(
        [bash, "--noprofile", "--norc", str(SCRIPT), str(fixture.resolve())],
        cwd=directory,
        env={**env, "CONTROL": "normal"},
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0
    assert "13 bytes" in result.stdout


def test_provenance_and_unmodified_resources() -> None:
    record = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    original_skill = canonical(MIRROR / "SKILL.md")
    original_script = canonical(MIRROR / "scripts/review_poster.sh")
    assert canonical(OVERLAY / "provenance/original.SKILL.md") == original_skill
    assert hashlib.sha256(original_skill).hexdigest() == record["original_skill_sha256"]
    assert hashlib.sha256(original_script).hexdigest() == record["original_script_sha256"]
    assert hashlib.sha256(canonical(SCRIPT)).hexdigest() == record["repaired_script_sha256"]
    assert hashlib.sha256(canonical(OVERLAY / "SKILL.md")).hexdigest() == record["repaired_skill_sha256"]
    assert hashlib.sha256(canonical(OVERLAY / "LICENSE")).hexdigest() == record["license_sha256"]
    overlay_skill = canonical(OVERLAY / "SKILL.md").decode("utf-8")
    assert "scripts/review_poster.sh" in overlay_skill
    assert record["source_mirror"] in overlay_skill
    assert "Mandatory agent tools" in overlay_skill
    assert not missing_markdown_links(OVERLAY, overlay_skill)
    assert record["model_performance_claim"] is False
    assert record["original_scanning_alerts_closed"] is False
    evidence = json.loads((ROOT / record["readiness_evidence"]).read_text(encoding="utf-8"))
    assert evidence["original_script_sha256"] == record["original_script_sha256"]
    assert evidence["repair_script_sha256"] == record["repaired_script_sha256"]
    assert any(not case["passed"] for case in evidence["original_control_cases"])
    assert evidence["repaired_controls"]["passed"] == evidence["repaired_controls"]["total"]
    assert evidence["model_performance_claim"] is False
    assert evidence["original_scanning_alerts_closed"] is False
