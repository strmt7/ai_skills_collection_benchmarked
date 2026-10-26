"""Protect source provenance and retained-result integrity independently of the SDK."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import run_pptx_retention_controls as runner
from test_pptx_retention import MARKDOWN


@pytest.fixture
def committed_source(tmp_path):
    root = tmp_path / "source"
    package = root / runner.PACKAGE
    package.mkdir(parents=True)
    (package / "main.py").write_bytes(b"print('fixture')\n")
    (package / ".gitignore").write_bytes(b"*.ignored\n")
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_"))
    }
    for arguments in (("init",), ("add", "."), ("commit", "--no-gpg-sign", "-m", "Independent input fixture")):
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=AI agent",
                "-c",
                "user.email=",
                "-c",
                "core.autocrlf=false",
                "-c",
                "core.hooksPath=NUL",
                "-C",
                str(root),
                *arguments,
            ],
            check=True,
            capture_output=True,
            env=environment,
        )
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    return root, commit


def test_source_matches_exact_git_bytes(committed_source):
    root, commit = committed_source
    snapshot = runner.verify_source(root, commit)
    assert snapshot["file_count"] == 2
    assert snapshot["bytes"] == len(b"print('fixture')\n*.ignored\n")


@pytest.mark.parametrize("change", ["dirty", "ignored", "untracked", "wrong-head", "subdirectory"])
def test_source_rejects_provenance_drift(committed_source, change):
    root, commit = committed_source
    if change == "dirty":
        (root / runner.PACKAGE / "main.py").write_bytes(b"different\n")
    elif change in {"ignored", "untracked"}:
        (root / runner.PACKAGE / ("extra.ignored" if change == "ignored" else "extra.py")).write_bytes(b"unadmitted")
    elif change == "wrong-head":
        commit = "0" * 40
    else:
        root = root / runner.PACKAGE
    with pytest.raises(ValueError):
        runner.verify_source(root, commit)


def test_source_byte_budget_stops_before_another_file(committed_source, monkeypatch):
    root, commit = committed_source
    visited = []
    original = runner.regular_file

    def record(root, name, directories):
        visited.append(name)
        return original(root, name, directories)

    monkeypatch.setattr(runner, "MAX_SOURCE_BYTES", 1)
    monkeypatch.setattr(runner, "regular_file", record)
    with pytest.raises(ValueError, match="byte budget"):
        runner.verify_source(root, commit)
    assert len(visited) == 1


@pytest.fixture
def retained_result(tmp_path):
    output = tmp_path / "result"
    output.mkdir()
    for name in runner.FROZEN_NAMES:
        (output / name).write_bytes(b"independent retained input")
    (output / "controller-before-execution.py").write_bytes(Path(runner.__file__).read_bytes())
    (output / "evaluator-before-execution.py").write_bytes(Path(runner.evaluator.__file__).read_bytes())
    (output / "process-control-before-execution.py").write_bytes(Path(runner.owned_python.__file__).read_bytes())
    runner.write_json(
        output / "task-before-execution.json", {"fixture_sha256": runner.sha256(output / "retention.pptx")}
    )
    rows = []
    for label in ("old", "new"):
        runner.write_json(output / f"{label}-source-manifest.json", {"commit": "a" * 40})
        workspace = output / label
        workspace.mkdir()
        (workspace / "retention.md").write_text(MARKDOWN, encoding="utf-8")
        logs = {}
        for name in (
            "integrity-guard.stdout.log",
            "integrity-guard.stderr.log",
            "converter.stdout.log",
            "converter.stderr.log",
        ):
            (workspace / name).write_bytes(b"native fixture log")
            logs[name] = runner.sha256(workspace / name)
        checks = {"cli_completes": True, **runner.evaluator.evaluate_markdown(MARKDOWN), "input_bytes_unchanged": True}
        rows.append(
            {
                "version": label,
                "source_commit": "a" * 40,
                "guard_exit_code": 0,
                "exit_code": 0,
                "owned_processes": {
                    phase: {
                        "windows_job": True,
                        "real_interpreter_gated_before_site": True,
                        "kill_on_close": True,
                        "active_processes_after_cleanup": 0,
                        "termination_reason": None,
                    }
                    for phase in ("guard", "converter")
                },
                "native_logs": logs,
                "markdown_sha256": runner.sha256(workspace / "retention.md"),
                "checks": checks,
                "passed": 11,
                "total": 11,
            }
        )
    result = {
        "schema_version": 1,
        "evidence_class": "native-component-content-retention-controls",
        "frozen_inputs": {name: runner.sha256(output / name) for name in runner.FROZEN_NAMES},
        "results": rows,
    }
    runner.write_json(output / "result.json", result)
    return output, result


def test_retained_component_result_is_recomputed(retained_result):
    output, result = retained_result
    assert runner.check_result(output) == result


@pytest.mark.parametrize(
    "tamper",
    [
        "fixture",
        "output",
        "log",
        "omit-input",
        "omit-log",
        "score",
        "boolean-score",
        "source",
        "boolean-exit",
        "numeric-check",
        "swapped-versions",
        "rehashed-corruption",
        "remaining-process",
        "false-cleanup-count",
        "false-termination",
    ],
)
def test_retained_result_rejects_tampering(retained_result, tamper):
    output, result = retained_result
    row = result["results"][1]
    if tamper == "fixture":
        (output / "retention.pptx").write_bytes(b"changed input")
    elif tamper in {"output", "rehashed-corruption"}:
        path = output / "new/retention.md"
        path.write_text(MARKDOWN.replace("North_Unit | 0", "North_Unit | -7.125"), encoding="utf-8")
        if tamper == "rehashed-corruption":
            row["markdown_sha256"] = runner.sha256(path)
    elif tamper == "log":
        (output / "new/converter.stderr.log").write_bytes(b"changed log")
    elif tamper == "omit-input":
        del result["frozen_inputs"]["retention.pptx"]
    elif tamper == "omit-log":
        del row["native_logs"]["converter.stderr.log"]
    elif tamper == "score":
        row["passed"] = 10
    elif tamper == "boolean-score":
        row["passed"] = True
    elif tamper == "source":
        row["source_commit"] = "b" * 40
    elif tamper == "boolean-exit":
        row["exit_code"] = False
    elif tamper == "numeric-check":
        row["checks"]["cli_completes"] = 1
    elif tamper == "remaining-process":
        row["owned_processes"]["converter"]["active_processes_after_cleanup"] = 1
    elif tamper == "false-cleanup-count":
        row["owned_processes"]["converter"]["active_processes_after_cleanup"] = False
    elif tamper == "false-termination":
        row["owned_processes"]["converter"]["termination_reason"] = "timeout"
    else:
        result["results"].reverse()
    runner.write_json(output / "result.json", result)
    with pytest.raises(ValueError):
        runner.check_result(output)


def test_check_cli_reports_missing_evidence(tmp_path, capsys):
    assert runner.main(["--check", "--output", str(tmp_path), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["protocol_complete"] is False


@pytest.mark.parametrize(
    "value",
    [
        [],
        {"schema_version": 1},
        {"schema_version": 1, "evidence_class": "native-component-content-retention-controls", "frozen_inputs": []},
    ],
)
def test_check_cli_reports_malformed_evidence(tmp_path, capsys, value):
    runner.write_json(tmp_path / "result.json", value)
    assert runner.main(["--check", "--output", str(tmp_path), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["errors"]


@pytest.mark.parametrize("name", ["../outside", "a/../outside", "a//b", "a\\b", "a:b", "/outside", "./a"])
def test_resource_paths_must_be_canonical(tmp_path, name):
    with pytest.raises(ValueError, match="noncanonical"):
        runner.regular_file(tmp_path, name)


def test_parent_checks_are_reused_within_one_scan(tmp_path):
    directory = tmp_path / "source/nested"
    directory.mkdir(parents=True)
    for name in ("a", "b"):
        (directory / name).write_bytes(b"fixture")
    checked: set[Path] = set()
    runner.regular_file(tmp_path, "source/nested/a", checked)
    assert directory in checked and directory.parent in checked
    # Once a separate scan starts, a directory replaced by a regular file fails.
    (directory / "a").unlink()
    (directory / "b").unlink()
    directory.rmdir()
    directory.write_bytes(b"not a directory")
    with pytest.raises(ValueError, match="non-directory"):
        runner.regular_file(tmp_path, "source/nested/b", set())
