"""Verify source provenance and observed Node CI component controls."""

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/latest-release-devops")
SOURCE = ROOT / "included/skills" / BASE / "azure-pipelines-generator"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-pipelines-node-ci"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-pipelines-node-ci-v1"
SOURCE_SHA = "1475c23454c1386ed0019d119233bc20b04ae32d7827bae53a7ef06801e52215"
CANDIDATE_SHA = "938e118734c95b4a9e11066cd9c973af703b7911ca9f9370a7525276f5208d2d"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_overlay_preserves_sources_and_binds_every_file() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert manifest["model_performance_claim"] is False
    assert manifest["azure_service_run"] is False
    assert normalized(SOURCE / "SKILL.md") == normalized(OVERLAY / "provenance/original.SKILL.md")
    assert normalized(SOURCE / "examples/basic-ci.yml") == normalized(OVERLAY / "provenance/original.basic-ci.yml")
    assert hashlib.sha256(normalized(SOURCE / "examples/basic-ci.yml")).hexdigest() == SOURCE_SHA
    assert sha(OVERLAY / "examples/node-ci.yml") == CANDIDATE_SHA
    for base, key, ignored in [(OVERLAY, "overlay_sha256", {"repair.json"}), (EVIDENCE, "evidence_sha256", set())]:
        actual = {
            p.relative_to(base).as_posix(): sha(p)
            for p in base.rglob("*")
            if p.is_file() and p.relative_to(base).as_posix() not in ignored
        }
        assert actual == manifest[key]


def test_pyyaml_lock_matches_the_repository_report_lock() -> None:
    text = (ROOT / "requirements-reports-lock.txt").read_text(encoding="utf-8")
    match = re.search(r"^pyyaml==6\.0\.3 \\\n(?:    --hash=sha256:[0-9a-f]{64}(?: \\)?\n)+", text, re.M)
    assert match is not None
    assert (EVIDENCE / "requirements-pyyaml.txt").read_text(encoding="utf-8") == match.group()


def test_recorded_linux_shell_guard_covers_empty_and_skipped_reports() -> None:
    result = json.loads((EVIDENCE / "linux-shell-guard.json").read_text(encoding="utf-8"))
    assert result["azure_service_run"] is False
    example = yaml.safe_load((OVERLAY / "examples/node-ci.yml").read_text(encoding="utf-8"))
    guard = next(step["script"] for step in example["steps"] if step.get("displayName") == "Require executed tests")
    assert result["guard_sha256"] == hashlib.sha256(guard.encode()).hexdigest()
    assert {item["case"]: item["exit_code"] for item in result["cases"]} == {
        "passing": 0,
        "failing": 0,
        "empty": 1,
        "skipped": 1,
        "malformed": 1,
    }


@pytest.mark.parametrize("system", ["windows", "linux"])
@pytest.mark.parametrize("version", ["24", "26"])
@pytest.mark.parametrize("npm_kind", ["bundled", "npm12"])
def test_recorded_local_controls(system: str, version: str, npm_kind: str) -> None:
    data = json.loads((EVIDENCE / "results" / f"{system}-node{version}-{npm_kind}.json").read_text(encoding="utf-8"))
    assert data["source_sha256"] == SOURCE_SHA and data["candidate_sha256"] == CANDIDATE_SHA
    assert data["platform"] == {"windows": "Windows", "linux": "Linux"}[system]
    assert data["node_version"] == {"24": "v24.22.2", "26": "v26.13.0"}[version]
    assert data["npm_version"] == ("12.2.1" if npm_kind == "npm12" else {"24": "11.19.1", "26": "11.20.0"}[version])
    assert data["azure_service_run"] is False and data["model_performance_tested"] is False
    assert data["source_lint_continue_on_error"] is True and data["candidate_lint_continue_on_error"] is False
    assert data["source_missing_result_setting_explicit"] is False and data["candidate_missing_result_fails"] is True
    calls = data["calls"]
    for name in [
        "prepare_lock",
        "candidate_install",
        "candidate_lint_pass",
        "plain_test",
        "candidate_test_pass",
        "candidate_test_empty",
        "candidate_test_skipped",
        "guard_pass",
    ]:
        assert calls[name]["exit_code"] == 0
    assert calls["candidate_lint_fail"]["exit_code"] == 23
    assert calls["original_test"]["exit_code"] == 9
    assert calls["candidate_test_fail"]["exit_code"] == 1
    assert calls["guard_empty"]["exit_code"] != 0 and calls["guard_skipped"]["exit_code"] != 0
    assert data["junit"]["passing_testcases"] >= 1 and data["junit"]["failures"] >= 1
    assert data["junit"]["empty_testcases"] == 0 and data["junit"]["skipped_testcases"] >= 1
    assert data["guard_execution"] == {"windows": "guard_body_directly", "linux": "example_bash_step"}[system]


@pytest.mark.parametrize(
    "case", ["source-drift", "lint-softened", "missing-report", "wrong-reporter", "wrong-runtime", "guard-removed"]
)
def test_control_rejects_changed_contract_before_starting_processes(tmp_path: Path, case: str) -> None:
    source = SOURCE / "examples/basic-ci.yml"
    proposed = yaml.safe_load((OVERLAY / "examples/node-ci.yml").read_text(encoding="utf-8"))
    if case == "source-drift":
        source = tmp_path / "source.yml"
        source.write_bytes(normalized(SOURCE / "examples/basic-ci.yml") + b"\n")
    else:
        proposed = copy.deepcopy(proposed)
        if case == "lint-softened":
            next(step for step in proposed["steps"] if step.get("script") == "npm run lint")["continueOnError"] = True
        elif case == "missing-report":
            next(step for step in proposed["steps"] if step.get("task") == "PublishTestResults@2")["inputs"][
                "failTaskOnMissingResultsFile"
            ] = False
        elif case == "wrong-reporter":
            next(step for step in proposed["steps"] if step.get("script", "").startswith("npm test"))["script"] = (
                "npm test"
            )
        elif case == "guard-removed":
            proposed["steps"] = [
                step for step in proposed["steps"] if step.get("displayName") != "Require executed tests"
            ]
        else:
            next(step for step in proposed["steps"] if step.get("task") == "UseNode@1")["inputs"]["version"] = "20.x"
    candidate = tmp_path / "candidate.yml"
    candidate.write_text(yaml.safe_dump(proposed, sort_keys=False), encoding="utf-8")
    output = tmp_path / "must-not-exist"
    result = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE / "reproduce.py"),
            "--source",
            str(source),
            "--candidate",
            str(candidate),
            "--node",
            str(tmp_path / "missing-node"),
            "--npm-cli",
            str(tmp_path / "missing-npm"),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    expected = "Original source bytes differ" if case == "source-drift" else "YAML does not match"
    assert result.returncode != 0 and expected in result.stderr and not output.exists()
