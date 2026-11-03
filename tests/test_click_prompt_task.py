"""Check the Click development calibration's evidence admission."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath, PureWindowsPath

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


def load_terminal_control():
    path = CONTROL.with_name("calibrate_terminal.py")
    terminal_spec = importlib.util.spec_from_file_location("click_terminal_calibrate", path)
    assert terminal_spec and terminal_spec.loader
    terminal = importlib.util.module_from_spec(terminal_spec)
    terminal_spec.loader.exec_module(terminal)
    return terminal


def test_terminal_screen_parser_distinguishes_erased_prompt() -> None:
    terminal = load_terminal_control()
    good = b"Question: abc\b\x1b[K\b\x1b[K\b\x1b[Kz\r\nRESULT=z\r\n"
    erased = b"Question: abc\b\x1b[K\b\x1b[K\r\x1b[Kz\r\nRESULT=z\r\n"
    positioned = b"Question: abc\r\x1b[13G\x1b[K\r\x1b[12G\x1b[K\r\x1b[11G\x1b[Kz\r\nRESULT=z\r\n"
    assert terminal.terminal_lines(good) == ["Question: z", "RESULT=z"]
    assert terminal.terminal_lines(erased) == ["z", "RESULT=z"]
    assert terminal.terminal_lines(positioned) == ["Question: z", "RESULT=z"]
    for bad in (b"\x1b[", b"\x1b[2J", b"\x00"):
        with pytest.raises(ValueError):
            terminal.terminal_lines(bad)


@pytest.mark.parametrize("backend", ["gnu", "libedit"])
def test_terminal_evidence_binds_source_inputs_traces_and_outcomes(backend: str) -> None:
    terminal = load_terminal_control()
    root = Path(__file__).resolve().parents[1]
    task = CONTROL.parent.parent
    evidence = root / "artifacts/research/2026-11-03/click-terminal-calibration-v1" / backend
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    assert result["source_commit"] == calibrate.COMMIT
    assert result["source_file_count"] == 142
    assert result["source_snapshot_sha256"] == "5b73c75d771e54933a4871bf73109f83161b8f6bc6689577a2850d93b9008c84"
    assert result["agent_performance_tested"] is False
    assert result["terminal"] == {"columns": 80, "rows": 24, "term": "xterm", "inputrc": "empty"}
    assert len(result["runtime"]["executable_sha256"]) == 64
    assert ("GNU readline" in result["runtime"]["readline_doc"]) == (backend == "gnu")
    for name, expected in result["control_inputs_sha256"].items():
        assert hashlib.sha256((task / name).read_bytes()).hexdigest() == expected
    planned = json.loads((task / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert set(result["variants"]) == {"upstream", "no-workaround", "entire-input-prompt"}
    for name, variant in result["variants"].items():
        stdout = (evidence / f"{name}.stdout").read_bytes()
        stderr = (evidence / f"{name}.stderr").read_bytes()
        assert hashlib.sha256(stdout).hexdigest() == variant["simulated_stdout_sha256"]
        assert hashlib.sha256(stderr).hexdigest() == variant["simulated_stderr_sha256"]
        assert variant["simulated_cases"] == 16
        assert calibrate.verify_results(stderr, planned, set(), 0) == []
        assert set(variant["cases"]) == {"prompt", "confirm"}
        for kind, observation in variant["cases"].items():
            transport = (evidence / f"{observation['trace']}.b64").read_text(encoding="ascii").strip()
            trace = base64.b64decode(transport, validate=True)
            assert hashlib.sha256(trace).hexdigest() == observation["sha256"]
            assert terminal.terminal_lines(trace) == observation["lines"]
            expected = ["Question: z", "RESULT=z"] if kind == "prompt" else ["Question: y", "RESULT=True"]
            assert observation["passed"] == (observation["lines"] == expected)
            expected_pass = name == "entire-input-prompt" or (name == "upstream" and backend == "gnu")
            assert observation["passed"] == expected_pass


def test_routing_input_names_are_portable_across_path_flavors() -> None:
    path = CONTROL.with_name("calibrate_routing.py")
    routing_spec = importlib.util.spec_from_file_location("click_routing_calibrate", path)
    assert routing_spec and routing_spec.loader
    routing = importlib.util.module_from_spec(routing_spec)
    routing_spec.loader.exec_module(routing)
    assert (
        routing.input_name(PureWindowsPath("C:/repo/controls/test.py"), PureWindowsPath("C:/repo"))
        == "controls/test.py"
    )
    assert routing.input_name(PurePosixPath("/repo/controls/test.py"), PurePosixPath("/repo")) == "controls/test.py"


@pytest.mark.parametrize("platform", ["windows", "linux"])
def test_routing_evidence_binds_controls_output_and_expected_failures(platform: str) -> None:
    root = Path(__file__).resolve().parents[1]
    task = CONTROL.parent.parent
    evidence = root / "artifacts/research/2026-11-03/click-routing-calibration-v2" / platform
    result = json.loads((evidence / "result.json").read_text(encoding="utf-8"))
    outputs = json.loads((evidence / "outputs.json").read_text(encoding="utf-8"))
    assert result["source_commit"] == calibrate.COMMIT
    assert result["source_file_count"] == 142
    assert result["source_snapshot_sha256"] == "5b73c75d771e54933a4871bf73109f83161b8f6bc6689577a2850d93b9008c84"
    assert result["agent_performance_tested"] is False
    assert len(result["runtime"]["executable_sha256"]) == 64
    for name, expected in result["control_inputs_sha256"].items():
        assert "\\" not in name
        assert hashlib.sha256((task / name).read_bytes()).hexdigest() == expected
    simulated_cases = json.loads((task / "cases.json").read_text(encoding="utf-8"))["cases"]
    routing_cases = [
        "test_confirm_to_stderr",
        "test_confirm_to_stdout",
        "test_prompt_to_stderr",
        "test_prompt_to_stdout",
    ]
    failures = {"test_confirm_to_stderr", "test_prompt_to_stderr"}
    assert set(result["variants"]) == {"upstream", "no-workaround", "entire-input-prompt", "err-ignored"}
    assert len(outputs) == 16
    for name, variant in result["variants"].items():
        assert set(variant["suites"]) == {"simulated", "routing"}
        for suite, observation in variant["suites"].items():
            stdout = base64.b64decode(outputs[f"{name}-{suite}.stdout"], validate=True)
            stderr = base64.b64decode(outputs[f"{name}-{suite}.stderr"], validate=True)
            assert hashlib.sha256(stdout).hexdigest() == observation["stdout_sha256"]
            assert hashlib.sha256(stderr).hexdigest() == observation["stderr_sha256"]
            cases = simulated_cases if suite == "simulated" else routing_cases
            expected = failures if suite == "routing" and name in {"entire-input-prompt", "err-ignored"} else set()
            assert observation["case_count"] == len(cases)
            assert observation["exit_code"] == int(bool(expected))
            assert calibrate.verify_results(stderr, cases, expected, observation["exit_code"]) == sorted(expected)
