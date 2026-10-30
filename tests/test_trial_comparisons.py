"""Independent controls for descriptive repetition-block comparisons."""

import pytest
from _trial_comparisons import compare_blocks


def attempt(repetition, condition, status, usage):
    """Create one deliberately small, already verified report record."""
    return {"repetition": repetition, "condition": condition, "status": status, "usage": usage}


def test_block_outcomes_and_success_conditional_token_differences():
    """Failures, missing usage and unscored runs retain their planned denominators."""

    def usage(inputs, outputs):
        """Construct a minimal pair of observed token totals."""
        return {"input_tokens": inputs, "output_tokens": outputs}

    rows = [
        attempt(1, "default", "task_passed", usage(100, 30)),
        attempt(1, "improved", "task_passed", usage(80, 20)),
        attempt(2, "default", "task_passed", usage(100, 30)),
        attempt(2, "improved", "task_failed", usage(50, 10)),
        attempt(3, "default", "harness_error", None),
        attempt(3, "improved", "task_passed", usage(90, 20)),
        attempt(4, "default", "task_passed", usage(100, 30)),
        attempt(4, "improved", "task_passed", None),
        attempt(5, "default", "task_failed", usage(100, 30)),
        attempt(5, "improved", "task_passed", usage(90, 20)),
        attempt(6, "default", "task_failed", usage(100, 30)),
        attempt(6, "improved", "task_failed", usage(90, 20)),
        attempt(7, "default", "task_passed", usage(120, 100)),
        attempt(7, "improved", "task_passed", usage(140, 130)),
    ]
    report = compare_blocks(rows, {"default", "improved"})
    assert report["baseline"] == "default"
    comparison = report["comparisons"]["improved"]
    assert comparison["planned_blocks"] == 7
    assert comparison["outcomes"] == {
        "both_passed": 3,
        "candidate_only_passed": 1,
        "baseline_only_passed": 1,
        "neither_passed": 1,
        "unscored": 1,
    }
    assert comparison["token_comparable_blocks"] == 2
    assert comparison["both_passed_usage_unavailable"] == 1
    assert comparison["token_deltas"]["input_tokens"] == {"median": 0, "min": -20, "max": 20}
    assert comparison["token_deltas"]["output_tokens"] == {"median": 10, "min": -10, "max": 30}
    assert [block["repetition"] for block in comparison["blocks"]] == list(range(1, 8))
    assert comparison["blocks"][1]["token_delta"] is None
    assert comparison["blocks"][3]["token_delta"] is None


def test_no_comparable_tokens_are_reported_as_unavailable():
    """Do not invent a zero delta when a condition has no usable token pair."""
    rows = [attempt(1, "default", "task_passed", None), attempt(1, "improved", "task_passed", None)]
    value = compare_blocks(rows, {"default", "improved"})["comparisons"]["improved"]
    assert value["token_comparable_blocks"] == 0
    assert value["both_passed_usage_unavailable"] == 1
    assert value["token_deltas"] is None


def test_no_named_default_condition_does_not_invent_a_baseline():
    """Comparison requires an explicit protocol condition named default."""
    rows = [attempt(1, "a", "task_passed", None), attempt(1, "b", "task_failed", None)]
    assert compare_blocks(rows, {"a", "b"}) == {"baseline": None, "comparisons": {}}


@pytest.mark.parametrize("change", ["missing", "duplicate", "unknown_status"])
def test_inconsistent_blocks_are_rejected(change):
    """Never silently pair duplicate, absent or unrecognized observations."""
    rows = [attempt(1, "default", "task_passed", None), attempt(1, "improved", "task_passed", None)]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(dict(rows[0]))
    else:
        rows[1]["status"] = "unknown"
    with pytest.raises(ValueError):
        compare_blocks(rows, {"default", "improved"})
