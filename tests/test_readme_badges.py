from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import update_readme_badges as badges

ROOT = Path(__file__).resolve().parents[1]
KARPATHY_BADGE_URL = (
    "https://img.shields.io/static/v1?label=&message=andrej-karpathy-skills&color=555&logo=github&logoColor=white"
)


def test_readme_badge_block_matches_generator() -> None:
    result = subprocess.run(
        [sys.executable, "tools/update_readme_badges.py", "--check"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_readme_uses_github_logo_static_karpathy_badge() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "<!-- BEGIN GENERATED BADGES -->" in readme
    assert "<!-- END GENERATED BADGES -->" in readme
    assert "[![andrej-karpathy-skills](" in readme
    assert KARPATHY_BADGE_URL in readme
    assert "https://github.com/forrestchang/andrej-karpathy-skills" in readme
    assert "https://img.shields.io/badge/andrej-karpathy-skills" not in readme


def test_python_badge_matches_supported_project_runtimes() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    versions = sorted(
        tuple(int(part) for part in classifier.rsplit(" :: ", 1)[1].split("."))
        for classifier in project["classifiers"]
        if classifier.startswith("Programming Language :: Python :: 3.")
    )
    oldest, newest = (".".join(str(part) for part in version) for version in (versions[0], versions[-1]))
    metadata = json.loads((ROOT / ".github/readme_badges.json").read_text(encoding="utf-8"))
    badge = next(badge for badge in metadata["badges"] if badge["alt"].startswith("Python "))
    assert badge["alt"] == f"Python {oldest}\N{EN DASH}{newest}"
    assert f"python-{oldest}%20%E2%80%93%20{newest}-" in badge["image"]
    assert project["requires-python"] == f">={oldest}"


def test_badge_writer_normalizes_crlf_without_changing_document_text(tmp_path: Path) -> None:
    metadata = tmp_path / badges.CANONICAL_METADATA_PATH
    metadata.parent.mkdir()
    metadata.write_bytes((ROOT / badges.CANONICAL_METADATA_PATH).read_bytes())
    text = "# Title\n\n" + badges.render_badge_block(badges.load_metadata(tmp_path)) + "\n\nUser content.\n"
    readme = tmp_path / badges.README_PATH
    original = text.replace("\n", "\r\n").encode("utf-8")
    readme.write_bytes(original)
    assert badges.update_readme(tmp_path, write=False) == 1
    assert readme.read_bytes() == original
    assert badges.update_readme(tmp_path, write=True) == 0
    assert readme.read_bytes() == text.encode("utf-8")
    assert badges.update_readme(tmp_path, write=False) == 0
