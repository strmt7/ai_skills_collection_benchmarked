from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
import validate_coverage_bundle as coverage
import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
XML = """<coverage lines-valid="1" lines-covered="1" line-rate="1">
<packages><package><classes><class filename="example.py"><lines>
<line number="1" hits="1"/></lines></class></classes></package></packages></coverage>"""


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "checkout"
    (root / "tools").mkdir(parents=True)
    (root / "tools/example.py").write_text("print('controlled fixture')\n", encoding="utf-8")
    directory = tmp_path / "reports"
    for name in ["linux", "windows"]:
        (directory / name).mkdir(parents=True)
        (directory / name / "coverage.xml").write_text(XML, encoding="utf-8")
    return root, directory


def test_reports_are_bound_to_actual_tool_sources(bundle):
    root, directory = bundle
    record, errors = coverage.validate_bundle(root, directory, 2)
    assert errors == []
    assert record["agent_performance_claim"] is False
    assert record["reports"][0]["source_sha256"] == {
        "tools/example.py": hashlib.sha256((root / "tools/example.py").read_bytes()).hexdigest()
    }


@pytest.mark.parametrize(
    "bad", ["missing", "traversal", "outside", "line", "negative-hits", "doctype", "utf16", "empty"]
)
def test_invalid_coverage_reports_are_rejected_without_hiding_valid_report(bundle, bad):
    root, directory = bundle
    xml = XML
    if bad == "missing":
        xml = xml.replace("example.py", "absent.py")
    elif bad == "traversal":
        xml = xml.replace("example.py", "../outside.py")
    elif bad == "outside":
        xml = xml.replace("example.py", "/outside.py")
    elif bad == "line":
        xml = xml.replace('number="1"', 'number="999"')
    elif bad == "negative-hits":
        xml = xml.replace('hits="1"', 'hits="-1"')
    elif bad == "doctype":
        xml = '<!DOCTYPE coverage [<!ENTITY fixture "data">]>' + xml
    elif bad == "empty":
        xml = '<coverage lines-valid="1"><packages/></coverage>'
    raw = xml.encode("utf-16" if bad == "utf16" else "utf-8")
    (directory / "linux/coverage.xml").write_bytes(raw)
    record, errors = coverage.validate_bundle(root, directory, 2)
    assert len(errors) == 1
    assert len(record["reports"]) == 1


def test_matrix_report_count_is_required(bundle):
    root, directory = bundle
    assert coverage.validate_bundle(root, directory, 3)[1]


def test_receipt_check_detects_source_change_and_emits_only_valid_report_paths(bundle, monkeypatch):
    root, directory = bundle
    monkeypatch.setattr(
        coverage.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, 0, "a" * 40)
    )
    output = root / "receipt.json"
    github = root / "github-output.txt"
    args = ["--root", str(root), "--directory", str(directory), "--expected-reports", "2", "--output", str(output)]
    assert coverage.main([*args, "--github-output", str(github)]) == 0
    assert github.read_text(encoding="utf-8").startswith("files=")
    assert coverage.main([*args, "--check"]) == 0
    (root / "tools/example.py").write_text("print('changed')\n", encoding="utf-8")
    assert coverage.main([*args, "--check"]) == 1
    assert json.loads(output.read_text(encoding="utf-8"))["source_revision"] == "a" * 40


def test_coverage_upload_keeps_oidc_out_of_test_jobs_and_requires_the_full_matrix():
    workflow = yaml.safe_load((REPOSITORY / ".github/workflows/offline-validation.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["coverage"]
    assert job["needs"] == "validate"
    assert job["permissions"] == {"contents": "read", "id-token": "write"}
    assert workflow["jobs"]["validate"].get("permissions", workflow["permissions"]) == {"contents": "read"}
    steps = job["steps"]
    upload = next(step for step in steps if step.get("uses", "").startswith("codecov/codecov-action@"))
    assert upload["with"]["use_oidc"] is True
    assert upload["with"]["fail_ci_if_error"] is True
    assert upload["with"]["disable_search"] is True
    matrix = workflow["jobs"]["validate"]["strategy"]["matrix"]
    count = len(matrix["os"]) * len(matrix["python-version"]) + len(matrix["include"])
    validate = next(step["run"] for step in steps if step.get("id") == "bundle")
    assert f"--expected-reports {count}" in validate
