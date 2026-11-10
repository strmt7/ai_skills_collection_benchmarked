"""Retained observations, rather than controller outcome labels, define usage."""

from __future__ import annotations

import json

import pytest
from _trial_execution_evidence import failure_measurements


def event(kind, **fields):
    return (json.dumps({"type": kind, **fields}) + "\n").encode()


def test_completed_usage_and_commands_survive_later_controller_failure():
    usage = {"input_tokens": 14, "cached_input_tokens": 3, "output_tokens": 8, "reasoning_tokens": 2}
    raw = event("item.completed", item={"type": "command_execution"}) + event("turn.completed", usage=usage)
    assert failure_measurements(raw, b'{"exit_code":17}') == {
        "usage": usage,
        "commands_completed": 1,
        "process_exit_code": 17,
        "transcript_error": None,
    }


def test_missing_observations_are_unavailable_not_zero():
    assert failure_measurements(None, None) == {
        "usage": None,
        "commands_completed": None,
        "process_exit_code": None,
        "transcript_error": None,
    }


def test_observed_zero_values_remain_distinct_from_missing_values():
    measured = failure_measurements(
        event("turn.completed", usage={"input_tokens": 0, "output_tokens": 0}), b'{"exit_code":0}'
    )
    assert measured["usage"] == {"input_tokens": 0, "output_tokens": 0}
    assert measured["commands_completed"] == 0 and measured["process_exit_code"] == 0


def test_partial_stream_retains_only_complete_observed_events():
    raw = event("item.completed", item={"type": "command_execution"}) + b'{"type":'
    measured = failure_measurements(raw, None)
    assert measured["commands_completed"] == 1 and measured["usage"] is None


@pytest.mark.parametrize(
    "raw",
    [
        b"not-json\n",
        b"\xff",
        event("turn.completed", usage={"input_tokens": True, "output_tokens": 0}),
        event("turn.completed") * 2,
        b'{"type":"turn.completed","type":"turn.completed"}\n',
    ],
)
def test_invalid_transcripts_never_create_usage_or_command_counts(raw):
    measured = failure_measurements(raw, None)
    assert measured["usage"] is None and measured["commands_completed"] is None
    assert isinstance(measured["transcript_error"], str) and measured["transcript_error"]


@pytest.mark.parametrize(
    "raw",
    [
        None,
        b"\xff",
        b"not-json",
        b"[]",
        b"null",
        b'{"exit_code":false}',
        b'{"exit_code":0.0}',
        b'{"exit_code":null}',
        b'{"exit_code":NaN}',
        b'{"exit_code":0,"exit_code":1}',
    ],
)
def test_unavailable_or_ambiguous_process_records_cannot_invent_an_exit_code(raw):
    assert failure_measurements(None, raw)["process_exit_code"] is None
