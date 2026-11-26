from __future__ import annotations

import json

import pytest
from collect_testeval_reply import collect_reply, extract_reply
from grade_testeval_submission import sha256

PROMPT = b"Return one test as the final message."
REPLY = "# a Unicode line separator inside this text: \u2028\ndef test_one():\r\n    assert 1 == 1\n"


def write_jsonl(path, events):
    path.write_bytes(b"".join(json.dumps(event, ensure_ascii=False).encode() + b"\n" for event in events))


@pytest.fixture
def native_turn(tmp_path):
    process = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "termination_reason": None,
        "exit_code": 0,
        "job_active_processes_after_cleanup": 0,
    }
    events = [
        {"type": "thread.started", "thread_id": "fixture"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "one", "type": "agent_message", "text": REPLY}},
        {"type": "turn.completed"},
    ]
    (tmp_path / "process.json").write_text(json.dumps(process), encoding="utf-8")
    (tmp_path / "input.native").write_bytes(PROMPT)
    (tmp_path / "last-message.native").write_bytes(REPLY.encode())
    write_jsonl(tmp_path / "transcript.jsonl", events)
    return tmp_path, process, events


def test_native_reply_preserves_unicode_and_original_newlines(native_turn):
    execution, _, _ = native_turn
    raw, evidence = extract_reply(execution, sha256(PROMPT))
    assert raw == REPLY.encode()
    assert evidence["message_item_id"] == "one"
    assert evidence["message_sha256"] == sha256(raw)
    assert evidence["prompt_sha256"] == sha256(PROMPT)


def test_native_reply_rejects_wrong_request_and_changed_export(native_turn):
    execution, _, _ = native_turn
    with pytest.raises(ValueError, match="frozen prompt"):
        extract_reply(execution, sha256(b"another request"))
    (execution / "last-message.native").write_bytes(REPLY.encode() + b"\n")
    with pytest.raises(ValueError, match="export differs"):
        extract_reply(execution, sha256(PROMPT))


def test_native_reply_rejects_unclosed_context(native_turn):
    execution, process, _ = native_turn
    process["job_active_processes_after_cleanup"] = 1
    (execution / "process.json").write_text(json.dumps(process), encoding="utf-8")
    with pytest.raises(ValueError, match="did not finish"):
        extract_reply(execution, sha256(PROMPT))


@pytest.mark.parametrize(
    "item", [{"id": "one", "type": "agent_message", "text": REPLY}, {"id": "later", "type": "command_execution"}]
)
def test_both_duplicate_reply_and_later_tool_prevent_sealing(native_turn, item):
    execution, _, events = native_turn
    events.insert(-1, {"type": "item.completed", "item": item})
    write_jsonl(execution / "transcript.jsonl", events)
    with pytest.raises(ValueError, match="no final assistant message"):
        extract_reply(execution, sha256(PROMPT))


def test_second_thread_prevents_sealing(native_turn):
    execution, _, events = native_turn
    events.insert(1, {"type": "thread.started", "thread_id": "different"})
    write_jsonl(execution / "transcript.jsonl", events)
    with pytest.raises(ValueError, match="complete native client turn"):
        extract_reply(execution, sha256(PROMPT))


def test_invalid_native_input_does_not_create_grading_evidence(tmp_path, monkeypatch):
    import collect_testeval_reply as replies
    import collect_testeval_submission as submissions

    monkeypatch.setattr(replies, "ROOT", tmp_path)
    monkeypatch.setattr(submissions, "ROOT", tmp_path)
    output = tmp_path / ".venv" / "new"
    foreign = tmp_path / "outside"
    foreign.mkdir()
    with pytest.raises(ValueError, match="disjoint controller"):
        collect_reply(foreign, foreign, foreign, sha256(PROMPT), foreign, foreign, foreign, output)
    assert not output.exists()
