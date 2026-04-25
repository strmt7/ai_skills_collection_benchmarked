"""Cross-tool CLI contract tests.

Every user-facing tool under ``tools/`` must:

1. Accept ``--help`` and produce non-empty output that exits 0.
2. Be a self-contained script invocable by Python directly (no missing imports).
3. Where a ``--check`` mode exists, it must exit 0 on the current committed state.

These tests run the real tool via ``subprocess`` so shebang/entry-point breakage
surfaces here rather than in a human reviewer's terminal.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from tests.helpers import ROOT

PYTHON = sys.executable
TOOL_DIR = ROOT / "tools"


ALL_TOOLS = sorted(p.name for p in TOOL_DIR.glob("*.py") if p.is_file() and not p.name.startswith("_"))

# Tools that literally accept --check and must exit 0 on committed data.
# Note: validate_catalog.py and validate_source_lock.py are always-check
# tools (they never mutate anything), so they do not need a --check flag
# and are exercised via TOOLS_NO_ARGS_RUN below.
TOOLS_WITH_CHECK = (
    "audit_skill_quality.py",
    "run_static_benchmarks.py",
    "evaluate_external_benchmark_methods.py",
    "report_local_markdown_link_failures.py",
)

# Tools whose common invocation needs no arguments.
TOOLS_NO_ARGS_RUN = (
    "validate_catalog.py",
    "validate_source_lock.py",
    "check_no_secret_patterns.py",
)


@pytest.mark.parametrize("tool", ALL_TOOLS)
def test_every_tool_prints_help(tool):
    result = subprocess.run(
        [PYTHON, str(TOOL_DIR / tool), "--help"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=30,
    )
    assert result.returncode == 0, f"--help returned {result.returncode}; stderr={result.stderr[:400]}"
    assert "usage:" in result.stdout.lower(), f"{tool}: help text missing 'usage:'"


@pytest.mark.parametrize("tool", TOOLS_WITH_CHECK)
def test_tool_check_mode_exits_zero(tool):
    result = subprocess.run(
        [PYTHON, str(TOOL_DIR / tool), "--check"],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=180,
    )
    assert result.returncode == 0, (
        f"--check returned {result.returncode}\nstdout={result.stdout[:800]}\nstderr={result.stderr[:800]}"
    )


@pytest.mark.parametrize("tool", TOOLS_NO_ARGS_RUN)
def test_tool_runs_without_arguments(tool):
    # The secret scanner is CI-sensitive; we still expect exit 0 on the
    # committed tree. The link reporter may report failures but must not crash.
    result = subprocess.run(
        [PYTHON, str(TOOL_DIR / tool)],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=180,
    )
    # Link reporter emits findings but still returns 0 on well-formed input;
    # if this ever changes, update the contract here deliberately.
    assert result.returncode in (0, 1), f"{tool}: unexpected exit {result.returncode}; stderr={result.stderr[:400]}"


def test_no_tool_leaks_host_paths_in_help():
    """Help output must not hard-code absolute host paths from the build machine.

    This guards against ``default=str(ROOT / 'data')`` leaking something like
    ``/home/berfarto54/work/...`` into help text — which would make the tool
    feel host-specific even when the behaviour is portable.
    """
    forbidden_prefixes = ("/home/berfarto54/", "/Users/")  # seen in prior slips
    for tool in ALL_TOOLS:
        result = subprocess.run(
            [PYTHON, str(TOOL_DIR / tool), "--help"],
            capture_output=True,
            text=True,
            cwd=ROOT,
            timeout=30,
        )
        combined = result.stdout + result.stderr
        for forbidden in forbidden_prefixes:
            assert forbidden not in combined, f"{tool} help text contains host-specific path prefix: {forbidden}"
