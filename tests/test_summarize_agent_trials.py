from __future__ import annotations

import json
import shutil
from typing import Any

import _trial_manifest
import pytest
import summarize_agent_trials as summary


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def matched(tmp_path):
    protocol: dict[str, Any] = {
        "protocol_version": 2,
        "task": {"id": "independent-fixture", "partition": "development"},
        "model": "requested-model",
        "reasoning_effort": "high",
        "grader_sha256": "a" * 64,
        "conditions": {"default": {}, "improved": {}},
        "planned_order": [{"repetition": 1, "conditions": ["default", "improved"]}],
        "limitations": [],
    }
    path = tmp_path / "protocol.json"
    write_json(path, protocol)
    digest = summary.sha256(path)
    write_json(
        path.with_name("protocol.grading.json"),
        {"manifest_version": 1, "protocol_sha256": digest, "grader_sha256": "a" * 64, "cases": ["independent"]},
    )
    trials = tmp_path / "trials"
    for condition in protocol["conditions"]:
        directory = trials / "repetition-1" / condition
        directory.mkdir(parents=True)
        write_json(directory / "launch.json", {"protocol_sha256": digest})
        for name in ("prompt.txt", "stderr.txt", "patch.diff"):
            (directory / name).write_text(name, encoding="utf-8")
        events = [
            {"type": "item.completed", "item": {"type": "command_execution"}},
            {"type": "turn.completed", "usage": {"input_tokens": 100, "cached_input_tokens": 20, "output_tokens": 30}},
        ]
        (directory / "transcript.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
        )
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
                "commands_completed": 1,
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


def replace_transcript(trials, text):
    directory = trials / "repetition-1/improved"
    transcript = directory / "transcript.jsonl"
    transcript.write_text(text, encoding="utf-8")
    result_path = directory / "result.json"
    result = summary.read_json(result_path)
    result["evidence_sha256"]["transcript.jsonl"] = summary.sha256(transcript)
    write_json(result_path, result)


def test_failure_and_unavailable_usage_keep_full_denominator(matched):
    path, trials = matched
    replace_transcript(trials, '{"type":"turn.started"}\n')
    edit_result(trials, status="harness_error", usage=None, process_exit_code=1, commands_completed=0)
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
        {"process_exit_code": "0"},
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


@pytest.mark.parametrize("changes", [{"commands_completed": 2}, {"usage": {"input_tokens": 101, "output_tokens": 30}}])
def test_reported_usage_and_command_count_must_match_transcript(matched, changes):
    path, trials = matched
    edit_result(trials, **changes)
    with pytest.raises(ValueError, match="transcript"):
        summary.summarize(path, trials)


@pytest.mark.parametrize(
    "transcript",
    [
        '{"type":"turn.started"}\n',
        '{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":20,"output_tokens":30}}\nnot-json\n',
        '{"type":"turn.completed","usage":{"input_tokens":100,"cached_input_tokens":20,"output_tokens":30}}\n{"type":',
        '{"type":"turn.completed"}\n{"type":"turn.completed"}\n',
        "[]\n",
        '{"type":"item.completed","item":null}\n',
        '{"type":"turn.started","type":"turn.completed"}\n',
        '{"type":"turn.completed","usage":{"input_tokens":NaN}}\n',
    ],
)
def test_a_pass_requires_a_complete_valid_transcript(matched, transcript):
    path, trials = matched
    replace_transcript(trials, transcript)
    with pytest.raises(ValueError, match="transcript"):
        summary.summarize(path, trials)


def test_interrupted_transcript_can_retain_truncated_last_event(matched):
    path, trials = matched
    replace_transcript(trials, '{"type":"turn.started"}\n{"type":')
    edit_result(trials, status="timed_out", usage=None, process_exit_code=1, commands_completed=0)
    assert summary.summarize(path, trials)["conditions"]["improved"]["task_passes"] == 0


def test_invalid_transcript_is_counted_as_a_verified_harness_error(matched):
    path, trials = matched
    replace_transcript(trials, '{"type":"turn.started"}\nnot-json\n{"type":"turn.completed"}\n')
    edit_result(
        trials,
        status="harness_error",
        usage=None,
        process_exit_code=0,
        commands_completed=None,
        transcript_error="transcript contains an invalid event on line 2",
        grader={"status": "harness_error", "error": "grading skipped because the transcript is invalid"},
    )
    condition = summary.summarize(path, trials)["conditions"]["improved"]
    assert condition["planned_attempts"] == 1
    assert condition["status_counts"] == {"harness_error": 1}
    assert condition["usage_unavailable_attempts"] == 1


def test_invalid_transcript_error_cannot_be_forged(matched):
    path, trials = matched
    replace_transcript(trials, '{"type":"turn.started"}\nnot-json\n')
    edit_result(
        trials,
        status="harness_error",
        usage=None,
        process_exit_code=0,
        commands_completed=None,
        transcript_error="different error",
    )
    with pytest.raises(ValueError, match="transcript"):
        summary.summarize(path, trials)


def test_transcript_usage_requires_exact_numeric_types(matched):
    path, trials = matched
    replace_transcript(
        trials,
        '{"type":"item.completed","item":{"type":"command_execution"}}\n'
        '{"type":"turn.completed","usage":{"input_tokens":100.0,"cached_input_tokens":20,"output_tokens":30}}\n',
    )
    with pytest.raises(ValueError, match="transcript"):
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


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "task_failed"},
        {
            "status": "task_failed",
            "grader": {
                "status": "task_failed",
                "checks": [{"case": "independent", "passed": True}],
                "checks_passed": 1,
                "checks_total": 1,
            },
        },
        {"status": "task_failed", "grader": {"status": "task_failed", "checks": []}},
        {"status": "invalid_scope", "scope_violations": []},
        {"process_exit_code": False},
        {
            "grader": {
                "status": "task_passed",
                "checks": [{"case": "independent", "passed": True}],
                "checks_passed": True,
                "checks_total": True,
            }
        },
    ],
)
def test_contradictory_failure_or_boolean_check_counts_are_rejected(matched, changes):
    path, trials = matched
    edit_result(trials, **changes)
    with pytest.raises(ValueError):
        summary.summarize(path, trials)


def test_verified_task_failure_is_kept_in_the_denominator(matched):
    path, trials = matched
    edit_result(
        trials,
        status="task_failed",
        grader={
            "status": "task_failed",
            "checks": [{"case": "independent", "passed": False}],
            "checks_passed": 0,
            "checks_total": 1,
        },
    )
    condition = summary.summarize(path, trials)["conditions"]["improved"]
    assert condition["planned_attempts"] == 1
    assert condition["status_counts"] == {"task_failed": 1}
    assert condition["task_passes"] == 0


def test_verified_scope_violation_is_kept_in_the_denominator(matched):
    path, trials = matched
    edit_result(trials, status="invalid_scope", scope_violations=["protected input changed"])
    condition = summary.summarize(path, trials)["conditions"]["improved"]
    assert condition["status_counts"] == {"invalid_scope": 1}
    assert condition["task_passes"] == 0


def test_matched_attempts_must_use_the_same_independent_cases(matched):
    path, trials = matched
    edit_result(
        trials,
        grader={
            "status": "task_passed",
            "checks": [{"case": "different", "passed": True}],
            "checks_passed": 1,
            "checks_total": 1,
        },
    )
    with pytest.raises(ValueError, match="same.*cases"):
        summary.summarize(path, trials)


def test_all_attempts_cannot_omit_the_same_frozen_case(matched):
    """Equal but incomplete case lists cannot shrink the grading denominator."""
    path, trials = matched
    manifest = path.with_name("protocol.grading.json")
    data = summary.read_json(manifest)
    data["cases"].append("second-case")
    write_json(manifest, data)
    with pytest.raises(ValueError, match="same.*grading cases"):
        summary.summarize(path, trials)


def test_new_protocol_requires_the_precommitted_case_set(matched):
    """A case manifest cannot be changed after a new protocol commits its digest."""
    path, trials = matched
    protocol = summary.read_json(path)
    protocol["protocol_version"] = 3
    protocol["grading_cases_sha256"] = _trial_manifest.case_digest(["independent"])
    write_json(path, protocol)
    manifest = path.with_name("protocol.grading.json")
    data = summary.read_json(manifest)
    data["protocol_sha256"] = summary.sha256(path)
    data["cases"] = ["different"]
    write_json(manifest, data)
    with pytest.raises(ValueError, match="committed case set"):
        summary.summarize(path, trials)


def test_case_commitment_has_a_portable_order_independent_encoding():
    """Case order does not alter the documented compact JSON digest."""
    expected = "138bf4722f7ae17122c7282d0eb156499d349940e129bd4cdf27c8ffdcbb3d25"
    assert _trial_manifest.case_digest(["alpha", "beta"]) == expected
    assert _trial_manifest.case_digest(["beta", "alpha"]) == expected


@pytest.mark.parametrize(
    "change",
    [
        {"manifest_version": True},
        {"protocol_sha256": "b" * 64},
        {"grader_sha256": "b" * 64},
        {"cases": []},
        {"cases": ["independent", "independent"]},
        {"cases": [" "]},
        {"cases": ["independent", None]},
    ],
)
def test_invalid_grading_manifest_is_rejected(matched, change):
    """The manifest must be unambiguous and bound to the protocol and grader."""
    path, trials = matched
    manifest = path.with_name("protocol.grading.json")
    data = summary.read_json(manifest)
    data.update(change)
    write_json(manifest, data)
    with pytest.raises(ValueError, match="grading manifest"):
        summary.summarize(path, trials)


def test_missing_or_duplicate_key_grading_manifest_is_rejected(matched):
    """A missing or ambiguous manifest cannot authorize a reported pass."""
    path, trials = matched
    manifest = path.with_name("protocol.grading.json")
    manifest.unlink()
    with pytest.raises(ValueError, match="grading manifest"):
        summary.summarize(path, trials)
    manifest.write_text('{"manifest_version": 1, "manifest_version": 1}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        summary.summarize(path, trials)


@pytest.mark.parametrize("document", ["protocol", "result", "launch"])
def test_duplicate_metadata_keys_are_rejected_even_when_evidence_hashes_match(matched, document):
    """Ambiguous JSON cannot become a scored report by updating its hash."""
    path, trials = matched
    directory = trials / "repetition-1/improved"
    target = path if document == "protocol" else directory / (document + ".json")
    field = "model" if document == "protocol" else "status" if document == "result" else "protocol_sha256"
    original = target.read_text(encoding="utf-8")
    target.write_text('{"' + field + '": "duplicate",' + original[1:], encoding="utf-8")
    if document == "launch":
        result_path = directory / "result.json"
        result = summary.read_json(result_path)
        result["evidence_sha256"]["launch.json"] = summary.sha256(target)
        write_json(result_path, result)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        summary.summarize(path, trials)


@pytest.mark.parametrize("changed", ["protocol", "manifest"])
def test_protocol_inputs_cannot_change_during_report_verification(matched, monkeypatch, changed):
    """Do not publish a report if its protocol inputs change mid-verification."""
    path, trials = matched
    target = path if changed == "protocol" else path.with_name("protocol.grading.json")
    verify = summary.verify_result

    def change_input(*args, **kwargs):
        result = verify(*args, **kwargs)
        target.write_text(target.read_text(encoding="utf-8") + " ", encoding="utf-8")
        return result

    monkeypatch.setattr(summary, "verify_result", change_input)
    with pytest.raises(ValueError, match="changed during verification"):
        summary.summarize(path, trials)


def test_report_check_detects_changed_publication(matched, tmp_path):
    path, trials = matched
    output = tmp_path / "report"
    argv = ["--protocol", str(path), "--trials", str(trials), "--output-dir", str(output)]
    assert summary.main(argv) == 0
    assert summary.main([*argv, "--check"]) == 0
    (output / "README.md").write_text("unsupported improvement claim", encoding="utf-8")
    assert summary.main([*argv, "--check"]) == 1
