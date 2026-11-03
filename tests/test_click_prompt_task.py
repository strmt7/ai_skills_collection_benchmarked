"""Check the Click development calibration's evidence admission."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

CONTROL = (
    Path(__file__).resolve().parents[1]
    / "benchmarks/agent-effectiveness/development/click-prompt-suffix-v1/controls/calibrate.py"
)
spec = importlib.util.spec_from_file_location("click_task_calibrate", CONTROL)
assert spec and spec.loader
calibrate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calibrate)


def test_upstream_patch_transport_preserves_bytes_and_rejects_invalid_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert hashlib.sha256(calibrate.upstream_patch()).hexdigest() == calibrate.PATCH_SHA256
    controls = tmp_path / "controls"
    controls.mkdir()
    monkeypatch.setattr(calibrate, "TASK", tmp_path)
    for malformed in ({"encoding": "base64", "patch": "x"}, {"encoding": "utf-8", "patch": 1}, {}):
        (controls / "upstream-patch.json").write_text(json.dumps(malformed), encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid upstream patch transport"):
            calibrate.upstream_patch()


def test_control_results_require_each_planned_case_and_matching_status() -> None:
    good = (
        b"test_a (__main__.Contract.test_a) ... ok\n"
        b"test_b (__main__.Contract.test_b) ... FAIL\n"
        b"FAIL: test_b (__main__.Contract.test_b)\n"
        b"Ran 2 tests in 0.001s\nFAILED (failures=1)\n"
    )
    assert calibrate.verify_results(good, ["test_a", "test_b"], {"test_b"}, 1) == ["test_b"]
    for broken in (
        good.replace(b"test_a (__main__.Contract.test_a) ... ok\n", b""),
        good.replace(b"test_a (__main__.Contract.test_a) ... ok\n", b"test_a (__main__.Contract.test_a) ... ok\n" * 2),
        good.replace(b"... FAIL", b"... ERROR"),
        good.replace(b"FAILED (failures=1)", b"OK"),
    ):
        with pytest.raises(ValueError, match="observations disagree"):
            calibrate.verify_results(broken, ["test_a", "test_b"], {"test_b"}, 1)
    with pytest.raises(ValueError, match="observations disagree"):
        calibrate.verify_results(good, ["test_a", "test_b"], {"test_b"}, 0)


def test_source_admission_detects_changed_missing_and_extra_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source"
    module = source / "src/click/termui.py"
    module.parent.mkdir(parents=True)
    data = b"pinned source\n"
    module.write_bytes(data)
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    task = tmp_path / "task"
    task.mkdir()
    tree = json.dumps({"files": {"src/click/termui.py": {"git_blob": blob}}}).encode()
    (task / "tree.json").write_bytes(tree)
    monkeypatch.setattr(calibrate, "TASK", task)
    monkeypatch.setattr(calibrate, "TREE_SHA256", hashlib.sha256(tree).hexdigest())
    monkeypatch.setattr(calibrate, "SOURCE_SHA256", hashlib.sha256(data).hexdigest())
    assert set(calibrate.verify_source(source)) == {"src/click/termui.py"}

    module.write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="differs"):
        calibrate.verify_source(source)
    module.write_bytes(data)
    extra = source / "extra.txt"
    extra.write_text("extra", encoding="utf-8")
    with pytest.raises(ValueError, match="extra files"):
        calibrate.verify_source(source)
    extra.unlink()
    module.unlink()
    with pytest.raises(ValueError, match="incomplete"):
        calibrate.verify_source(source)
