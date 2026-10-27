"""Check that extractor controls reject incomplete or duplicated evidence."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def controls():
    path = Path(__file__).resolve().parents[1] / "benchmarks/dependency-regressions/docs_from_code_controls.py"
    spec = importlib.util.spec_from_file_location("docs_from_code_controls", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_signature_requires_parameter_kinds_defaults_and_return_type(controls):
    assert controls.signature_matches(
        'def sample(name: str = "x", /, count: int = 1, *args: str, flag: bool = False, **kwargs: int) -> str'
    )
    assert not controls.signature_matches("def sample(name: str, count: int, flag: bool) -> str")
    assert not controls.signature_matches("def sample(")


def test_duplicate_routes_do_not_satisfy_the_control(controls):
    result = {
        "cases": {
            "flask": {"routes": [{"method": "GET", "path": "/users"}] * 2 + [{"method": "POST", "path": "/users"}]},
            "false_decorator": {"routes": []},
            "fastapi_mount": {"routes": [{"method": "GET", "path": "/api/v1/users"}]},
            "invalid_source": {"exit_code": 1, "output_exists": False},
            "signature": {
                "signature": 'def sample(name: str = "x", /, count: int = 1, *args: str, flag: bool = False, **kwargs: int) -> str'
            },
        }
    }
    assessments = controls.assess(result)
    assert assessments["flask_routes"] is False
    assert all(value for name, value in assessments.items() if name != "flask_routes")
