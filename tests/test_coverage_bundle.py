from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tomllib
from importlib.metadata import version
from pathlib import Path

import pytest
import record_coverage_shard as producer
import validate_coverage_bundle as coverage
import yaml
from packaging.requirements import Requirement

REPOSITORY = Path(__file__).resolve().parents[1]
REVISION = "a" * 40
LINUX, WINDOWS = "coverage-linux", "coverage-windows"
XML = """<coverage lines-valid="1" lines-covered="1" line-rate="1">
<packages><package><classes><class filename="example.py"><lines>
<line number="1" hits="1"/></lines></class></classes></package></packages></coverage>"""


def _write_fixture_receipt(root: Path, path: Path, relative: str = "tools/example.py") -> None:
    receipt = {
        "schema_version": 1,
        "source_revision": REVISION,
        "lane": path.parent.name,
        "report_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_sha256": {relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()},
    }
    path.with_name("coverage-shard.json").write_text(json.dumps(receipt), encoding="utf-8")


@pytest.fixture
def bundle(tmp_path):
    """Create two reports and one checked-out source file for bundle controls."""
    root = tmp_path / "checkout"
    (root / "tools").mkdir(parents=True)
    (root / "tools/example.py").write_text("print('controlled fixture')\n", encoding="utf-8")
    directory = tmp_path / "reports"
    for name in [LINUX, WINDOWS]:
        report = directory / name / "coverage.xml"
        report.parent.mkdir(parents=True)
        report.write_text(XML, encoding="utf-8")
        _write_fixture_receipt(root, report)
    return root, directory


def test_reports_are_bound_to_actual_tool_sources(bundle):
    """Record the actual bytes of each source referenced by a valid report."""
    root, directory = bundle
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert errors == []
    assert record["agent_performance_claim"] is False
    assert record["reports"][0]["source_sha256"] == {
        "tools/example.py": hashlib.sha256((root / "tools/example.py").read_bytes()).hexdigest()
    }


def test_benign_xml_comment_containing_dtd_text_is_not_a_declaration(bundle):
    """Text inside a comment is not a DTD and must not invalidate coverage."""
    root, directory = bundle
    xml = XML.replace("<packages>", "<!-- <!DOCTYPE harmless> --><packages>", 1)
    (directory / LINUX / "coverage.xml").write_text(xml, encoding="utf-8")
    _write_fixture_receipt(root, directory / LINUX / "coverage.xml")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert not errors
    assert len(record["reports"]) == 2


@pytest.mark.parametrize(
    "declaration",
    [
        "<!DOCTYPE coverage>",
        '<!DOCTYPE coverage [<!ENTITY a "x">]>',
        '<!DOCTYPE coverage SYSTEM "file:///not-a-real-file">',
        '<!DOCTYPE coverage [<!ENTITY % a SYSTEM "file:///not-a-real-file">%a;]>',
    ],
)
def test_dtds_and_entities_are_rejected_before_upload(bundle, declaration):
    """External resources and all DTDs remain forbidden in coverage data."""
    root, directory = bundle
    (directory / LINUX / "coverage.xml").write_text(declaration + XML, encoding="utf-8")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert len(errors) == 1
    assert "DTD/entity declarations are not coverage data" in errors[0]
    assert len(record["reports"]) == 1


@pytest.mark.parametrize(
    "bad_xml",
    [
        XML.replace('<line number="1" hits="1"/>', ""),
        XML.replace('lines-valid="1"', 'lines-valid="2"'),
        XML.replace('lines-covered="1"', 'lines-covered="0"'),
        XML.replace('line-rate="1"', 'line-rate="0"'),
        XML.replace('line-rate="1"', 'line-rate="NaN"'),
        XML.replace('<line number="1" hits="1"/>', '<line number="1" hits="1"/>' * 2),
        XML.replace("</class>", '</class><class filename="tools/example.py"><lines/></class>'),
        XML.replace('filename="example.py"', 'filename="./example.py"'),
    ],
    ids=["missing-lines", "total", "covered", "rate", "nonfinite", "duplicate-line", "duplicate-source", "alias"],
)
def test_report_rejects_contradictory_metrics_or_repeated_observations(bundle, bad_xml):
    """Claimed coverage must agree with distinct lines in canonical sources."""
    root, directory = bundle
    (directory / LINUX / "coverage.xml").write_text(bad_xml, encoding="utf-8")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert len(errors) == 1
    assert len(record["reports"]) == 1


def test_zero_covered_lines_is_valid_when_the_report_says_so(bundle):
    """A coherent zero-coverage result must not be inflated or rejected."""
    root, directory = bundle
    xml = XML.replace('lines-covered="1"', 'lines-covered="0"').replace('line-rate="1"', 'line-rate="0"')
    (directory / LINUX / "coverage.xml").write_text(xml.replace('hits="1"', 'hits="0"'), encoding="utf-8")
    _write_fixture_receipt(root, directory / LINUX / "coverage.xml")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert not errors
    assert len(record["reports"]) == 2


@pytest.mark.parametrize(("rate", "accepted"), [("0.3333", True), ("0.3334", False)])
def test_line_rate_allows_coverage_py_rounding_without_accepting_contradictions(bundle, rate, accepted):
    """Allow the four-decimal rate emitted by coverage.py for one of three lines."""
    root, directory = bundle
    (root / "tools/example.py").write_text("first\nsecond\nthird\n", encoding="utf-8")
    xml = XML.replace('lines-valid="1"', 'lines-valid="3"').replace('line-rate="1"', f'line-rate="{rate}"')
    xml = xml.replace(
        '<line number="1" hits="1"/>',
        '<line number="1" hits="1"/>' + '<line number="2" hits="0"/><line number="3" hits="0"/>',
    )
    (directory / LINUX / "coverage.xml").write_text(xml, encoding="utf-8")
    _write_fixture_receipt(root, directory / LINUX / "coverage.xml")
    _write_fixture_receipt(root, directory / WINDOWS / "coverage.xml")
    _, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert (not errors) is accepted


def test_reports_must_cover_the_same_source_set(bundle):
    """A truncated matrix report must not silently narrow coverage scope."""
    root, directory = bundle
    (root / "tools/other.py").write_text("pass\n", encoding="utf-8")
    (directory / WINDOWS / "coverage.xml").write_text(XML.replace("example.py", "other.py"), encoding="utf-8")
    _write_fixture_receipt(root, directory / WINDOWS / "coverage.xml", "tools/other.py")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert len(errors) == 1
    assert "source set differs" in errors[0]
    assert len(record["reports"]) == 1


@pytest.mark.parametrize("unsafe", ["bad,report/coverage.xml", "bad\nreport/coverage.xml", "bad\rreport/coverage.xml"])
def test_report_paths_cannot_inject_upload_list_or_github_outputs(tmp_path, unsafe):
    """Report paths must fit both the comma-separated upload list and output protocol."""
    with pytest.raises(ValueError, match="cannot be represented safely"):
        coverage._report_document(tmp_path / unsafe, tmp_path)


def test_unsafe_report_path_does_not_publish_upload_outputs(bundle, monkeypatch):
    """A filename that would change Codecov's file list must fail the upload gate."""
    root, directory = bundle
    (directory / LINUX).rename(directory / "coverage-linux,extra")
    monkeypatch.setattr(coverage, "source_revision", lambda _root: REVISION)
    output, github = root / "receipt.json", root / "github-output.txt"
    assert (
        coverage.main(
            [
                "--root",
                str(root),
                "--directory",
                str(directory),
                "--expected-reports",
                "2",
                "--output",
                str(output),
                "--github-output",
                str(github),
            ]
        )
        == 1
    )
    assert not output.exists()
    assert not github.exists()


@pytest.mark.parametrize(
    "bad", ["missing", "traversal", "outside", "line", "negative-hits", "doctype", "utf16", "empty"]
)
def test_invalid_coverage_reports_are_rejected_without_hiding_valid_report(bundle, bad):
    """Collect one invalid-report error while retaining the other valid report."""
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
    (directory / LINUX / "coverage.xml").write_bytes(raw)
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION)
    assert len(errors) == 1
    assert len(record["reports"]) == 1


def test_matrix_report_count_is_required(bundle):
    """Reject a bundle that does not contain every expected matrix report."""
    root, directory = bundle
    assert coverage.validate_bundle(root, directory, 3, REVISION)[1]


def test_receipt_check_detects_source_change_and_emits_only_valid_report_paths(bundle, monkeypatch):
    """Detect changed source bytes when rechecking a previously saved receipt."""
    root, directory = bundle
    monkeypatch.setattr(coverage, "source_revision", lambda _root: REVISION)
    output = root / "receipt.json"
    github = root / "github-output.txt"
    args = ["--root", str(root), "--directory", str(directory), "--expected-reports", "2", "--output", str(output)]
    assert coverage.main([*args, "--github-output", str(github)]) == 0
    assert github.read_text(encoding="utf-8").startswith("files=")
    assert coverage.main([*args, "--check"]) == 0
    (root / "tools/example.py").write_text("print('changed')\n", encoding="utf-8")
    assert coverage.main([*args, "--check"]) == 1
    assert json.loads(output.read_text(encoding="utf-8"))["source_revision"] == REVISION


@pytest.mark.parametrize(
    "change", ["receipt_missing", "xml", "same_layout_source", "revision", "lane", "duplicate_key"]
)
def test_bundle_requires_the_exact_producer_receipt(bundle, change):
    """Reject unproven reports even if their line counts still match."""
    root, directory = bundle
    report = directory / LINUX / "coverage.xml"
    receipt_path = report.with_name("coverage-shard.json")
    if change == "receipt_missing":
        receipt_path.unlink()
    elif change == "xml":
        report.write_text(XML + "<!-- different report bytes -->", encoding="utf-8")
    elif change == "same_layout_source":
        (root / "tools/example.py").write_text("print('another source on one line')\n", encoding="utf-8")
        _write_fixture_receipt(root, directory / WINDOWS / "coverage.xml")
    elif change == "duplicate_key":
        raw = receipt_path.read_text(encoding="utf-8")
        receipt_path.write_text(
            raw.replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'), encoding="utf-8"
        )
    else:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        key, value = ("source_revision", "b" * 40) if change == "revision" else ("lane", WINDOWS)
        receipt[key] = value
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    record, errors = coverage.validate_bundle(root, directory, 2, REVISION, expected_lanes=[LINUX, WINDOWS])
    assert len(record["reports"]) == len(errors) == 1


def test_bundle_requires_the_declared_lane_set(bundle):
    """An unintended lane cannot fill a missing lane's slot."""
    root, directory = bundle
    _, errors = coverage.validate_bundle(root, directory, 2, REVISION, expected_lanes=[LINUX, "coverage-macos"])
    assert errors == ["Coverage reports must match the declared matrix lanes"]


@pytest.mark.parametrize("outcome", ["success", "test_failure", "source_change", "untracked_measurement"])
def test_coverage_is_sealed_only_for_the_original_successful_run(bundle, monkeypatch, tmp_path, outcome):
    """Check pre/post source binding and the producer's failure behavior."""
    root, _ = bundle
    out = tmp_path / "coverage-output"
    source = root / "tools/example.py"
    original = {source.relative_to(root).as_posix(): hashlib.sha256(source.read_bytes()).hexdigest()}
    if outcome == "untracked_measurement":
        original = {"tools/different.py": next(iter(original.values()))}
    after = ("b" * 40 if outcome == "source_change" else REVISION, original)
    observations = iter([(REVISION, original), after])
    monkeypatch.setattr(producer, "snapshot_sources", lambda _root: next(observations))

    def pytest_run(command, *, cwd, env, check):
        assert cwd == root and check is False
        assert env["COVERAGE_FILE"] == str(out / ".coverage")
        assert command[1:6] == ["-m", "pytest", "-q", "-n", "2"]
        assert command[6] == "--cov=tools"
        assert command[-1] == f"--cov-report=xml:{out / 'coverage.xml'}"
        (out / "coverage.xml").write_text(XML, encoding="utf-8")
        return subprocess.CompletedProcess(command, 1 if outcome == "test_failure" else 0)

    monkeypatch.setattr(producer.subprocess, "run", pytest_run)
    if outcome in {"source_change", "untracked_measurement"}:
        with pytest.raises(ValueError, match="changed during pytest|absent from the producer"):
            producer.measure(root, out, LINUX, ["-q", "-n", "2"])
    else:
        assert producer.measure(root, out, LINUX, ["-q", "-n", "2"]) == (0 if outcome == "success" else 1)
    receipt = out / "coverage-shard.json"
    assert receipt.exists() == (outcome == "success")
    if outcome == "success":
        assert json.loads(receipt.read_text(encoding="utf-8")) == {
            "schema_version": 1,
            "source_revision": REVISION,
            "lane": LINUX,
            "report_sha256": hashlib.sha256((out / "coverage.xml").read_bytes()).hexdigest(),
            "source_sha256": original,
        }


@pytest.fixture
def committed_tool_checkout(tmp_path):
    """Use a fresh Git fixture to exercise the producer's actual source discovery."""
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git is required to exercise coverage source binding")
    root = tmp_path / "native-checkout"
    (root / "tools").mkdir(parents=True)
    (root / ".gitattributes").write_bytes(b"* text eol=lf\n")
    (root / "tools/__init__.py").write_bytes(b"")
    (root / "tools/example.py").write_bytes(b"def add(left, right):\n    return left + right\n")
    (root / "test_example.py").write_bytes(
        b"from tools.example import add\n\ndef test_add():\n    assert add(2, 3) == 5\n"
    )
    (root / "pytest.ini").write_bytes(b"[pytest]\n")
    git_env = {key: val for key, val in os.environ.items() if not key.upper().startswith("GIT_")}
    git_env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    git_cmd = [
        git,
        "-C",
        str(root),
        "-c",
        "core.longpaths=true",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "user.name=Coverage Test Fixture",
        "-c",
        "user.email=coverage-test@example.invalid",
    ]
    for args in (["init", "--initial-branch=main"], ["add", "."], ["commit", "--no-verify", "-qm", "Fixture input"]):
        subprocess.run([*git_cmd, *args], env=git_env, check=True, capture_output=True, timeout=30)
    return root


def test_producer_and_consumer_cli_with_real_git_and_coverage(committed_tool_checkout, tmp_path, monkeypatch):
    """Exercise the public CLI with real pytest-cov output and an exact Git revision."""
    root = committed_tool_checkout
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    directory = tmp_path / "reports"
    target = directory / LINUX
    assert (
        producer.main(
            [
                "--root",
                str(root),
                "--directory",
                str(target),
                "--lane",
                LINUX,
                "--pytest-args",
                "-q",
                "-p",
                "pytest_cov.plugin",
                "test_example.py",
            ]
        )
        == 0
    )
    output, github = tmp_path / "bundle.json", tmp_path / "github-output.txt"
    assert (
        coverage.main(
            [
                "--root",
                str(root),
                "--directory",
                str(directory),
                "--expected-reports",
                "1",
                "--expected-lanes",
                LINUX,
                "--output",
                str(output),
                "--github-output",
                str(github),
            ]
        )
        == 0
    )
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["source_revision"] == coverage.source_revision(root)
    assert (
        receipt["reports"][0]["source_sha256"]["tools/example.py"]
        == hashlib.sha256((root / "tools/example.py").read_bytes()).hexdigest()
    )
    assert github.read_text(encoding="utf-8") == f"files={(target / 'coverage.xml').as_posix()}\n"


def test_producer_stops_before_pytest_when_tracked_source_changed(committed_tool_checkout, tmp_path, capsys):
    """A dirty measuring checkout must fail before creating any report."""
    root = committed_tool_checkout
    (root / "tools/example.py").write_bytes(b"def add(left, right):\n    return left - right\n")
    target = tmp_path / "reports"
    assert producer.main(["--root", str(root), "--directory", str(target), "--lane", LINUX]) == 1
    assert not target.exists()
    assert "unchanged tools checkout" in capsys.readouterr().err


def test_coverage_upload_keeps_oidc_out_of_test_jobs_and_requires_the_full_matrix():
    """Keep upload identity restricted and validate every matrix artifact first."""
    workflow = yaml.safe_load((REPOSITORY / ".github/workflows/offline-validation.yml").read_text(encoding="utf-8"))
    job = workflow["jobs"]["coverage"]
    assert job["needs"] == "validate"
    assert job["permissions"] == {"contents": "read", "id-token": "write"}
    assert workflow["jobs"]["validate"].get("permissions", workflow["permissions"]) == {"contents": "read"}
    steps = job["steps"]
    installs = [step for step in steps if step.get("name") == "Install hashed coverage parser"]
    uploads = [step for step in steps if step.get("uses", "").startswith("codecov/codecov-action@")]
    validations = [step for step in steps if step.get("id") == "bundle"]
    assert len(installs) == len(uploads) == len(validations) == 1
    install, upload, validation = installs[0], uploads[0], validations[0]
    assert "--require-hashes -r requirements-coverage-lock.txt" in install["run"]
    assert "--only-binary=:all:" in install["run"]
    assert upload["with"]["use_oidc"] is True
    assert upload["with"]["fail_ci_if_error"] is True
    assert upload["with"]["disable_search"] is True
    validation_job = workflow["jobs"]["validate"]
    producer_steps = validation_job["steps"]
    measurement = next(step for step in producer_steps if step.get("name") == "Run tests (with coverage)")
    artifact = next(step for step in producer_steps if step.get("name") == "Upload producer coverage bundle")
    assert producer_steps.index(measurement) < producer_steps.index(artifact)
    assert "record_coverage_shard.py --directory coverage-output" in measurement["run"]
    assert "--pytest-args -q -n auto" in measurement["run"]
    assert artifact["with"]["path"].splitlines() == [
        "coverage-output/coverage.xml",
        "coverage-output/coverage-shard.json",
    ]
    assert "if" not in artifact
    matrix = validation_job["strategy"]["matrix"]
    lanes = {f"coverage-{os}-{version}" for os in matrix["os"] for version in matrix["python-version"]} | {
        f"coverage-{item['os']}-{item['python-version']}" for item in matrix["include"]
    }
    args = validation["run"].split()
    lane_start = args.index("--expected-lanes") + 1
    assert set(args[lane_start : args.index("--output")]) == lanes
    assert args[args.index("--expected-reports") + 1] == str(len(lanes))
    assert steps.index(install) < steps.index(validation) < steps.index(upload)


def test_coverage_parser_lock_matches_installed_test_dependency():
    """The minimal CI parser lock must agree with the supported test extra."""
    project = tomllib.loads((REPOSITORY / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = [Requirement(item) for item in project["project"]["optional-dependencies"]["test"]]
    parsers = [item for item in requirements if item.name == "defusedxml"]
    pins = [
        line.strip().removesuffix("\\").strip()
        for line in (REPOSITORY / "requirements-coverage-lock.txt").read_text(encoding="utf-8").splitlines()
        if line.startswith("defusedxml==")
    ]
    assert len(parsers) == len(pins) == 1
    parser, locked = parsers[0], Requirement(pins[0])
    installed_version = version("defusedxml")
    assert installed_version in parser.specifier
    assert installed_version in locked.specifier
