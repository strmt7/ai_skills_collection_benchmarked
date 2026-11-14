"""Check portable artifact admission independently of native process execution."""

from __future__ import annotations

import pytest
from _windows_trial_process import verify_write_io_budget


@pytest.fixture
def observed():
    return {
        "write_io_limit_bytes": 65536,
        "job_write_io_bytes": 4096,
        "write_io_overshoot_bytes": 0,
        "write_io_observation_error": None,
        "write_io_enforcement": "polled_job_transfer_accounting",
        "hard_storage_quota": False,
        "termination_reason": None,
    }


def test_complete_in_budget_observation_is_admitted(observed):
    verify_write_io_budget(observed, 65536)


@pytest.mark.parametrize(
    "field,value",
    [
        ("write_io_limit_bytes", True),
        ("write_io_limit_bytes", 65537),
        ("job_write_io_bytes", None),
        ("job_write_io_bytes", True),
        ("job_write_io_bytes", -1),
        ("job_write_io_bytes", 2**64),
        ("write_io_overshoot_bytes", False),
        ("write_io_overshoot_bytes", 1),
        ("write_io_enforcement", "hard_quota"),
        ("hard_storage_quota", 0),
        ("hard_storage_quota", True),
        ("termination_reason", "write_io_limit"),
        ("termination_reason", "resource_observation_error"),
    ],
)
def test_inconsistent_budget_observations_are_rejected(observed, field, value):
    observed[field] = value
    with pytest.raises(ValueError):
        verify_write_io_budget(observed, 65536)


def test_missing_accounting_fields_cannot_claim_success(observed):
    del observed["write_io_observation_error"]
    with pytest.raises(ValueError):
        verify_write_io_budget(observed, 65536)


def test_over_budget_process_must_retain_interruption_and_overshoot(observed):
    observed.update(job_write_io_bytes=131072, write_io_overshoot_bytes=65536)
    with pytest.raises(ValueError):
        verify_write_io_budget(observed, 65536)
    observed["termination_reason"] = "write_io_limit"
    verify_write_io_budget(observed, 65536)


@pytest.mark.parametrize(
    "diagnostic",
    [
        {"api": "QueryInformationJobObject", "information_class": 8, "winerror": 5},
        {"api": "QueryInformationJobObject", "information_class": 8, "expected_bytes": 96, "returned_bytes": 0},
    ],
)
def test_accounting_failure_remains_unmeasured_and_interrupted(observed, diagnostic):
    observed.update(
        job_write_io_bytes=None,
        write_io_overshoot_bytes=None,
        write_io_observation_error=diagnostic,
        termination_reason="resource_observation_error",
    )
    verify_write_io_budget(observed, 65536)
    observed["termination_reason"] = None
    with pytest.raises(ValueError):
        verify_write_io_budget(observed, 65536)
