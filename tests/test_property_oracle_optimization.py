"""Verify standalone oracle controls under normal and optimized Python."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "benchmarks/dependency-regressions/property_oracle_controls.py"
PROBE = """
import importlib.util, json, operator, pathlib, sys, types
spec = importlib.util.spec_from_file_location('property_controls', pathlib.Path(sys.argv[1]))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
if sys.argv[2] == 'broken':
    module.operator = types.SimpleNamespace(add=lambda a, b: 999, sub=operator.sub)
rows = module.controls()
print(json.dumps({'optimize': not __debug__, 'first': rows[0], 'all_passed': all(row['passed'] for row in rows)}))
"""


@pytest.mark.parametrize("optimized", [False, True])
@pytest.mark.parametrize("broken", [False, True])
def test_oracle_controls_detect_broken_reference_in_both_execution_modes(optimized: bool, broken: bool) -> None:
    """A broken reference must never pass simply because Python uses -O."""
    command = [
        sys.executable,
        "-I",
        "-B",
        *(["-O"] if optimized else []),
        "-c",
        PROBE,
        str(SCRIPT),
        "broken" if broken else "clean",
    ]
    process = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=60, check=False)
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["optimize"] is optimized
    assert result["first"]["control"] == "independent_simple_expression_is_not_a_tautology"
    assert result["first"]["passed"] is not broken
    assert result["all_passed"] is not broken
    if broken:
        assert "reference addition disagrees" in result["first"]["error"]
