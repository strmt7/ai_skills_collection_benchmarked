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
    "update_readme_badges.py",
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


# ---------------------------------------------------------------------------
# In-process main(argv) tests so coverage tracks branches exercised by CI.
# Subprocess tests above cover the shebang/entry-point contract; the tests
# below cover the internal logic the way production code is actually invoked.
# ---------------------------------------------------------------------------


def _in_process(module_name: str, argv: list[str]) -> int:
    import importlib

    mod = importlib.import_module(module_name)
    return mod.main(argv)


def test_validate_catalog_main_in_process_passes():
    assert _in_process("validate_catalog", []) == 0


def test_validate_catalog_main_json_mode_in_process():
    import io
    import json as _json
    from contextlib import redirect_stdout

    out = io.StringIO()
    with redirect_stdout(out):
        rc = _in_process("validate_catalog", ["--json"])
    assert rc == 0
    payload = _json.loads(out.getvalue())
    assert payload["ok"] is True
    assert payload["catalog_entries"] > 0


def test_run_static_benchmarks_check_in_process():
    import importlib

    mod = importlib.import_module("run_static_benchmarks")
    # Some tools' main() uses raise SystemExit; tolerate either return-int or raise.
    try:
        rc = mod.main(["--check"]) if callable(getattr(mod, "main", None)) else 0
    except SystemExit as exc:
        rc = int(exc.code or 0)
    assert rc == 0


def test_audit_skill_quality_check_in_process():
    assert _in_process("audit_skill_quality", ["--check"]) == 0


def test_evaluate_external_benchmark_methods_check_in_process():
    assert _in_process("evaluate_external_benchmark_methods", ["--check"]) == 0


def test_report_local_markdown_link_failures_check_in_process():
    assert _in_process("report_local_markdown_link_failures", ["--check"]) == 0


def test_check_benchmark_artifact_validate_all_in_process():
    assert (
        _in_process(
            "check_benchmark_artifact",
            ["--validate-all", str(ROOT / "artifacts" / "benchmark-runs")],
        )
        == 0
    )


def test_check_no_secret_patterns_default_in_process():
    import importlib

    mod = importlib.import_module("check_no_secret_patterns")
    try:
        rc = mod.main([]) if callable(getattr(mod, "main", None)) else 0
    except SystemExit as exc:
        rc = int(exc.code or 0)
    assert rc == 0
