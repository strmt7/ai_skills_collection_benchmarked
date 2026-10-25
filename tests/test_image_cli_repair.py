from __future__ import annotations

import runpy
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "included/improved/skills/cover-image-workflow-current"
MIRROR = ROOT / "included/skills/by-category/creative-media-design/reddit-verified-gtm-registry/blog-cover-image-cli"
HELPER = runpy.run_path(str(OVERLAY / "scripts/prepare_cli.py"))


def source_copy(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    shutil.copytree(MIRROR, source)
    return source


def test_repair_preserves_source_and_changes_only_declared_code(tmp_path):
    source = source_copy(tmp_path)
    original = {file.relative_to(source): file.read_bytes() for file in source.rglob("*") if file.is_file()}
    output = tmp_path / "prepared"
    receipt = HELPER["prepare"](source, output)
    assert len(receipt["source_files"]) == 20
    assert receipt["real_provider_qualified"] is False
    assert receipt["agent_efficacy_scored"] is False
    changed = set()
    for relative, data in original.items():
        assert (source / relative).read_bytes() == data
        if (output / relative).read_bytes() != data:
            changed.add(relative.as_posix())
    assert changed == {"bin/cli.js", "src/imageValidator.js"}
    assert (output / "repair-preparation.json").is_file()


@pytest.mark.parametrize("mutation", ["change", "remove", "extra"])
def test_source_drift_fails_before_output_is_created(tmp_path, mutation):
    source = source_copy(tmp_path)
    file = source / "src/imageValidator.js"
    if mutation == "change":
        file.write_bytes(file.read_bytes() + b"\n// changed\n")
    elif mutation == "remove":
        file.unlink()
    else:
        (source / "unexpected.txt").write_text("extra", encoding="utf-8")
    output = tmp_path / "prepared"
    with pytest.raises(ValueError, match="source"):
        HELPER["prepare"](source, output)
    assert not output.exists()


def test_existing_output_is_preserved(tmp_path):
    source = source_copy(tmp_path)
    output = tmp_path / "prepared"
    output.mkdir()
    (output / "user-file").write_bytes(b"preserve this")
    with pytest.raises(ValueError, match="new"):
        HELPER["prepare"](source, output)
    assert list(output.iterdir()) == [output / "user-file"]
    assert (output / "user-file").read_bytes() == b"preserve this"


def test_source_overlap_rejected_before_writing(tmp_path):
    source = source_copy(tmp_path)
    with pytest.raises(ValueError, match="overlap"):
        HELPER["prepare"](source, source / "nested")
    assert not (source / "nested").exists()


def test_portable_text_newlines_are_accepted_without_rewriting_source(tmp_path):
    source = source_copy(tmp_path)
    file = source / "bin/cli.js"
    windows_bytes = file.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    file.write_bytes(windows_bytes)
    HELPER["prepare"](source, tmp_path / "prepared")
    assert file.read_bytes() == windows_bytes


def test_preparer_cli_returns_failure_for_incomplete_source(tmp_path, capsys):
    source = tmp_path / "source"
    source.mkdir()
    assert HELPER["main"](["--source", str(source), "--output", str(tmp_path / "prepared")]) == 1
    assert '"prepared": false' in capsys.readouterr().out
    assert not (tmp_path / "prepared").exists()


def test_changed_replacement_fails_before_output_is_created(tmp_path, monkeypatch):
    source = source_copy(tmp_path)
    overlay = tmp_path / "overlay"
    shutil.copytree(OVERLAY, overlay)
    asset = overlay / "assets/cli.js"
    asset.write_bytes(asset.read_bytes() + b"\n// changed\n")
    monkeypatch.setitem(HELPER["prepare"].__globals__, "OVERLAY", overlay)
    with pytest.raises(ValueError, match="replacement hash mismatch"):
        HELPER["prepare"](source, tmp_path / "prepared")
    assert not (tmp_path / "prepared").exists()
