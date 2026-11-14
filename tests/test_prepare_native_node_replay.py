from __future__ import annotations

import json
from pathlib import Path

import prepare_native_node_replay as builder
import pytest
from _native_replay_assets import file_sha256
from test_native_image_archive import archive_fixture


def test_offline_check_binds_every_artifact_without_engine_or_network_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / ".venv/replay"
    output.mkdir(parents=True)
    packet = output / "image.tar"
    digest, identity = archive_fixture(packet)
    (output / "runtime.json").write_text(
        json.dumps({"image_reference": identity, "image_archive": str(packet), "image_archive_sha256": digest})
    )
    artifacts = {path.name: {"bytes": path.stat().st_size, "sha256": file_sha256(path)} for path in output.iterdir()}
    (output / "result.json").write_text(
        json.dumps({"passed": True, "source_sha256": {}, "artifacts": artifacts, "image_id": identity})
    )
    monkeypatch.setattr(builder, "implementation", lambda root: {})
    assert builder.check(tmp_path, output)["passed"]
    (output / "unexpected").write_bytes(b"unrecorded")
    with pytest.raises(ValueError, match="unexpected files"):
        builder.check(tmp_path, output)


def test_setup_failure_keeps_diagnostics_only_in_its_new_owned_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(builder.sys, "platform", "win32")
    monkeypatch.setattr(builder.platform, "machine", lambda: "AMD64")
    monkeypatch.setattr(builder, "implementation", lambda root: {})
    output = tmp_path / ".venv/new-replay"
    with pytest.raises(FileNotFoundError):
        builder.prepare(tmp_path, tmp_path / "absent-runtime", output)
    assert json.loads((output / "failure.json").read_bytes())["passed"] is False
    before = (output / "failure.json").read_bytes()
    with pytest.raises(FileExistsError):
        builder.prepare(tmp_path, tmp_path / "absent-runtime", output)
    assert (output / "failure.json").read_bytes() == before


def test_setup_rejects_an_output_outside_owned_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(builder.sys, "platform", "win32")
    monkeypatch.setattr(builder.platform, "machine", lambda: "AMD64")
    with pytest.raises(ValueError, match="checkout's .venv"):
        builder.prepare(tmp_path, tmp_path / "runtime", tmp_path / "outside")
    assert not (tmp_path / "outside").exists()


def test_main_returns_failure_for_an_absent_receipt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert builder.main(["--check", "--output", str(tmp_path / "absent")]) == 1
    assert json.loads(capsys.readouterr().out)["passed"] is False
