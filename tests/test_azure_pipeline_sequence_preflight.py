"""Independent command-line controls for literal pipeline sequence preflight."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/latest-release-devops")
SOURCE = ROOT / "included/skills" / BASE / "azure-pipelines-validator"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-pipelines-sequence-preflight"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-pipeline-sequence-preflight-v1"
PREFLIGHT = OVERLAY / "preflight.py"


def test_manifest_and_observed_source_bindings():
    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert not manifest["azure_service_run"] and not manifest["model_performance_claim"]
    for original, saved in [
        ("SKILL.md", "original.SKILL.md"),
        ("scripts/validate_syntax.py", "original.validate_syntax.py"),
    ]:
        assert (SOURCE / original).read_bytes().replace(b"\r\n", b"\n") == (
            OVERLAY / "provenance" / saved
        ).read_bytes().replace(b"\r\n", b"\n")
    for base, key, ignore in [(OVERLAY, "overlay_sha256", {"repair.json"}), (EVIDENCE, "evidence_sha256", set())]:
        assert {
            p.relative_to(base).as_posix(): digest(p)
            for p in base.rglob("*")
            if p.is_file() and p.relative_to(base).as_posix() not in ignore
        } == manifest[key]
    assert (OVERLAY / "requirements.txt").read_bytes() == (
        ROOT / "artifacts/repaired-skill-readiness/azure-pipelines-node-ci-v1/requirements-pyyaml.txt"
    ).read_bytes()


@pytest.mark.parametrize("platform_name", ["windows", "linux"])
def test_recorded_paired_controls(platform_name):
    result = json.loads((EVIDENCE / f"{platform_name}.json").read_text(encoding="utf-8"))
    assert result["platform"].lower() == platform_name
    assert result["preflight_sha256"] == hashlib.sha256(PREFLIGHT.read_bytes()).hexdigest()
    assert (
        result["source_sha256"]
        == hashlib.sha256((OVERLAY / "provenance/original.validate_syntax.py").read_bytes()).hexdigest()
    )
    assert (
        not result["azure_service_run"]
        and not result["other_validator_components_run"]
        and not result["agent_performance_tested"]
    )
    cases = {case["case"]: case for case in result["cases"]}
    assert len(cases) == 9
    for name in ("bare_step", "bare_job", "bare_stage", "nested_bare_step"):
        assert cases[name]["exit_code"] == 0 and cases[name]["preflight_exit_code"] == 1
    for name in ("conditional_mapping", "step_list_insertion"):
        assert cases[name]["preflight_status"] == "indeterminate"
    assert cases["missing_task_version"]["exit_code"] == 1
    assert cases["missing_task_version"]["preflight_status"] == "no_shape_issues"
    assert result["cp1252"]["unicode_encode_error"] and result["cp1252"]["preflight_exit_code"] == 0


def invoke(tmp_path: Path, content: bytes, *, cp1252: bool = False):
    fixture = tmp_path / "pipeline.yml"
    fixture.write_bytes(content)
    env = dict(os.environ)
    if cp1252:
        env.update(PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    cmd = [sys.executable, "-X", "utf8=0"] if cp1252 else [sys.executable, "-I", "-X", "utf8"]
    result = subprocess.run([*cmd, str(PREFLIGHT), str(fixture), "--json"], env=env, capture_output=True, timeout=15)
    payload = json.loads(result.stdout)
    assert payload["azure_schema_validated"] is False
    return result, payload


@pytest.mark.parametrize(
    "content",
    [
        b"steps:\n  - script: echo hello\n",
        b"stages:\n  - stage: A\n    jobs:\n      - job: B\n        steps:\n          - bash: echo hello\n",
        b"steps:\n  - task: ExampleTask\n",  # Task-version validation is outside the preflight's scope.
    ],
)
def test_static_shapes(tmp_path, content):
    result, payload = invoke(tmp_path, content)
    assert (result.returncode, payload["status"]) == (0, "no_shape_issues")


@pytest.mark.parametrize(
    ("content", "path", "line", "column"),
    [
        (b"steps:\n  - echo hello\n", "$root.steps[0]", 2, 5),
        (b"jobs:\n  - build\n", "$root.jobs[0]", 2, 5),
        (b"stages:\n  - build\n", "$root.stages[0]", 2, 5),
        (b"jobs:\n  - job: A\n    steps:\n      - echo hello\n", "$root.jobs[0].steps[0]", 4, 9),
        (b"steps:\n  - null\n", "$root.steps[0]", 2, 5),
        (b"steps:\n  - 42\n", "$root.steps[0]", 2, 5),
        (b"steps:\n  - [one, two]\n", "$root.steps[0]", 2, 5),
    ],
)
def test_literal_shapes(tmp_path, content, path, line, column):
    result, payload = invoke(tmp_path, content)
    assert (result.returncode, payload["status"]) == (1, "issues")
    issue = payload["issues"][0]
    assert (issue["path"], issue["line"], issue["column"]) == (path, line, column)


@pytest.mark.parametrize(
    "content",
    [
        b"steps:\n  - ${{ parameters.preBuild }}\n",
        b"steps:\n  - ${{ if eq(parameters.run, true) }}:\n      - script: echo hello\n",
        b"steps:\n  - template: steps.yml\n",
        b"steps: ${{ parameters.steps }}\n",
        b"steps:\n  - unknown: value\n",
        b"jobs:\n  - deployment: A\n",
        b"jobs:\n  - job: A\n    strategy: {}\n    steps: []\n",
        b"steps: []\nsteps: []\n",
        b"steps: []\njobs: []\n",
        b"trigger: none\n",
    ],
)
def test_unresolved_forms_are_not_claimed_valid(tmp_path, content):
    result, payload = invoke(tmp_path, content)
    assert (result.returncode, payload["status"]) == (2, "indeterminate")
    assert payload["deferred"]
    assert not payload["issues"]


def test_conditional_and_mixed_findings(tmp_path):
    result, payload = invoke(tmp_path, b"steps:\n  - ${{ if eq(a, b) }}:\n      - script: x\n  - bare\n")
    assert (result.returncode, payload["status"]) == (1, "issues")
    assert len(payload["issues"]) == len(payload["deferred"]) == 1


@pytest.mark.parametrize("content", [b"steps: [\n", b"- item\n", b"steps: \xff\n"])
def test_invalid_input(tmp_path, content):
    result, payload = invoke(tmp_path, content)
    assert (result.returncode, payload["status"]) == (3, "invalid_input")
    assert payload["error"]


def test_missing_file(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", str(PREFLIGHT), str(tmp_path / "missing"), "--json"], capture_output=True, timeout=15
    )
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "invalid_input"


def test_explicit_cp1252_output(tmp_path):
    result, payload = invoke(tmp_path, "steps:\n  - script: echo café\n".encode(), cp1252=True)
    assert result.returncode == 0
    assert result.stdout.isascii()
    assert payload["status"] == "no_shape_issues"
