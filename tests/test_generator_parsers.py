"""Lock-in tests for the argparse contracts of generator/evaluator tools.

Each tool's ``build_parser()`` is the documented surface other scripts and CI
hooks call. If a flag is renamed or removed by accident, this test fails before
CI breaks.
"""

from __future__ import annotations

import importlib

import pytest

# tools/ on sys.path via tests/conftest.py


@pytest.fixture(scope="module")
def runtime_batch():
    return importlib.import_module("create_independent_runtime_batch")


@pytest.fixture(scope="module")
def source_proof():
    return importlib.import_module("create_source_proof_batch")


@pytest.fixture(scope="module")
def external_benchmark():
    return importlib.import_module("evaluate_external_benchmark_methods")


def _flag_names(parser):
    """Return the set of long-form ``--flag`` option strings on a parser."""
    flags: set[str] = set()
    for action in parser._actions:
        for opt in action.option_strings:
            if opt.startswith("--"):
                flags.add(opt)
    return flags


def test_runtime_batch_parser_keeps_documented_flags(runtime_batch):
    flags = _flag_names(runtime_batch.build_parser())
    expected = {
        "--help",
        "--limit",
        "--batch-name",
        "--batch-slug",
        "--risk-level",
        "--include-visual",
        "--category-spread",
        "--avoid-existing-independent",
    }
    assert expected <= flags, f"missing flags: {expected - flags}"


def test_runtime_batch_parser_accepts_dry_help(runtime_batch):
    parser = runtime_batch.build_parser()
    # parse_args with empty argv must populate every action with its default.
    ns = parser.parse_args([])
    assert ns.limit == 10
    assert ns.include_visual is False


def test_source_proof_parser_keeps_documented_flags(source_proof):
    flags = _flag_names(source_proof.build_parser())
    expected = {"--help", "--batch-name", "--limit", "--catalog-commit"}
    assert expected <= flags


def test_source_proof_parser_default_invocation(source_proof):
    ns = source_proof.build_parser().parse_args([])
    assert ns.limit == 10
    assert ns.catalog_commit is None


def test_external_benchmark_parser_keeps_documented_flags(external_benchmark):
    flags = _flag_names(external_benchmark.build_parser())
    expected = {"--help", "--check", "--registry-only"}
    assert expected <= flags


def test_external_benchmark_main_check_signature(external_benchmark):
    """main(argv) must run the offline --check path and exit 0 on committed data."""
    rc = external_benchmark.main(["--check"])
    assert rc == 0


def test_audit_skill_quality_main_check_signature():
    """audit_skill_quality.main accepts an argv list (testable signature)."""
    audit = importlib.import_module("audit_skill_quality")
    rc = audit.main(["--check"])
    assert rc == 0
