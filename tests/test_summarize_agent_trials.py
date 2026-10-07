from __future__ import annotations

import json
import shutil
from typing import Any

import pytest
import summarize_agent_trials as summary


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def matched(tmp_path):
    protocol: dict[str, Any] = {
        "task": {"id": "independent-fixture", "partition": "development"},
        "model": "requested-model",
        "reasoning_effort": "high",
        "conditions": {"default": {}, "improved": {}},
        "planned_order": [{"repetition": 1, "conditions": ["default", "improved"]}],
        "limitations": [],
    }
    path = tmp_path / "protocol.json"
    write_json(path, protocol)
    digest = summary.sha256(path)
    trials = tmp_path / "trials"
    for condition in protocol["conditions"]:
        directory = trials / "repetition-1" / condition
        directory.mkdir(parents=True)
        write_json(directory / "launch.json", {"protocol_sha256": digest})
        for name in ("transcript.jsonl", "prompt.txt", "stderr.txt", "patch.diff"):
            (directory / name).write_text(name, encoding="utf-8")
        cache = directory / "submission/tools/__pycache__/fixture.cpython-312.pyc"
        cache.parent.mkdir(parents=True)
        cache.write_bytes(b"captured-bytecode-evidence-is-never-executed")
        hashes = {
            file.relative_to(directory).as_posix(): summary.sha256(file)
            for file in directory.rglob("*")
            if file.is_file()
        }
        write_json(
            directory / "result.json",
            {
                "protocol_sha256": digest,
                "task_id": protocol["task"]["id"],
                "partition": "development",
                "condition": condition,
                "status": "task_passed",
                "model_requested": "requested-model",
                "reasoning_effort_requested": "high",
                "grader": {
                    "status": "task_passed",
                    "checks": [{"case": "independent", "passed": True}],
                    "checks_passed": 1,
                    "checks_total": 1,
                },
                "process_exit_code": 0,
                "scope_violations": [],
                "evidence_collection_errors": [],
                "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 30},
                "evidence_sha256": hashes,
            },
        )
    return path, trials


def edit_result(trials, target_condition="improved", **changes):
    path = trials / "repetition-1" / target_condition / "result.json"
    result = summary.read_json(path)
    result.update(changes)
    write_json(path, result)


def test_failure_and_unavailable_usage_keep_full_denominator(matched):
    path, trials = matched
    edit_result(trials, status="harness_error", usage=None, process_exit_code=1)
    report = summary.summarize(path, trials)
    improved = report["conditions"]["improved"]
    assert improved["planned_attempts"] == 1
    assert improved["task_passes"] == 0
    assert improved["usage_unavailable_attempts"] == 1
    assert improved["token_statistics"] is None
    assert report["quality_superiority_established"] is False


def test_missing_planned_run_cannot_be_dropped(matched):
    path, trials = matched
    (trials / "repetition-1/improved/result.json").rename(trials / "unfinished.json")
    with pytest.raises(ValueError, match="has not completed"):
        summary.summarize(path, trials)


def test_unplanned_attempt_cannot_be_selected_or_pooled(matched):
    path, trials = matched
    shutil.copyfile(trials / "repetition-1/default/result.json", trials / "extra-result.json")
    extra = trials / "unplanned"
    extra.mkdir()
    shutil.copyfile(trials / "repetition-1/default/result.json", extra / "result.json")
    with pytest.raises(ValueError, match="unplanned results"):
        summary.summarize(path, trials)


@pytest.mark.parametrize(
    "changes",
    [
        {"condition": "default"},
        {"protocol_sha256": "b" * 64},
        {"scope_violations": ["protected input changed"]},
        {"evidence_collection_errors": ["missing output"]},
        {"usage": {"input_tokens": 10, "cached_input_tokens": 11, "output_tokens": 3}},
        {"usage": {"input_tokens": True, "output_tokens": 3}},
    ],
)
def test_inconsistent_metadata_or_usage_cannot_pass(matched, changes):
    path, trials = matched
    edit_result(trials, **changes)
    with pytest.raises(ValueError):
        summary.summarize(path, trials)


def test_modified_evidence_cannot_pass(matched):
    path, trials = matched
    (trials / "repetition-1/improved/prompt.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="hash changed"):
        summary.summarize(path, trials)


def test_archived_bytecode_keeps_git_transport_verifiable(matched, tmp_path):
    path, trials = matched
    initial = summary.summarize(path, trials, package_caches=True)
    transported = tmp_path / "fresh-checkout"
    shutil.copytree(trials, transported, ignore=shutil.ignore_patterns("__pycache__"))
    assert summary.summarize(path, transported) == initial


def test_archive_does_not_hide_missing_source_evidence(matched):
    path, trials = matched
    summary.summarize(path, trials, package_caches=True)
    (trials / "repetition-1/improved/prompt.txt").rename(trials / "missing-prompt.txt")
    with pytest.raises(ValueError, match="missing evidence"):
        summary.summarize(path, trials)


@pytest.mark.parametrize("name", ["../outside", "/outside", "a/../b", "a//b", "C:/outside", "a\\b"])
def test_unsafe_evidence_paths_fail_closed(tmp_path, name):
    with pytest.raises(ValueError):
        summary.evidence_path(tmp_path, name)


def test_duplicate_external_checks_are_rejected(matched):
    path, trials = matched
    edit_result(
        trials,
        grader={
            "status": "task_passed",
            "checks": [{"case": "same", "passed": True}, {"case": "same", "passed": True}],
            "checks_passed": 2,
            "checks_total": 2,
        },
    )
    with pytest.raises(ValueError, match="unique nonempty"):
        summary.summarize(path, trials)


def test_report_check_detects_changed_publication(matched, tmp_path):
    path, trials = matched
    output = tmp_path / "report"
    argv = ["--protocol", str(path), "--trials", str(trials), "--output-dir", str(output)]
    assert summary.main(argv) == 0
    assert summary.main([*argv, "--check"]) == 0
    (output / "README.md").write_text("unsupported improvement claim", encoding="utf-8")
    assert summary.main([*argv, "--check"]) == 1
