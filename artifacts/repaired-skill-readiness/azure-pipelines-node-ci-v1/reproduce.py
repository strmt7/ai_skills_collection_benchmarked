"""Run source-bound local Node CI controls; this does not execute Azure Pipelines."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

SOURCE_SHA = "1475c23454c1386ed0019d119233bc20b04ae32d7827bae53a7ef06801e52215"


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--npm-cli", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.read_bytes().replace(b"\r\n", b"\n")
    candidate = args.candidate.read_bytes().replace(b"\r\n", b"\n")
    if digest(source) != SOURCE_SHA:
        raise ValueError("Original source bytes differ from the pinned sample")
    original, proposed = yaml.safe_load(source), yaml.safe_load(candidate)
    source_lint = next(item for item in original["steps"] if item.get("script") == "npm run lint")
    source_test = next(item for item in original["steps"] if item.get("script") == "npm test -- --coverage")
    source_publisher = next(item for item in original["steps"] if item.get("task") == "PublishTestResults@2")
    scripts = [step["script"] for step in proposed["steps"] if "script" in step]
    lint = next(item for item in proposed["steps"] if item.get("script") == "npm run lint")
    publisher = next(item for item in proposed["steps"] if item.get("task") == "PublishTestResults@2")
    setup = next(item for item in proposed["steps"] if item.get("task") == "UseNode@1")
    guard = (
        "python3 - <<'PY'\n"
        "import xml.etree.ElementTree as ET\n"
        "root = ET.parse('junit.xml').getroot()\n"
        "executed = [case for case in root.iter('testcase') if case.find('skipped') is None]\n"
        "if not executed:\n"
        "    raise SystemExit('No executed test cases in junit.xml')\n"
        "PY\n"
    )
    expected = [
        "npm ci",
        "npm run lint",
        "npm test -- --test-reporter=junit --test-reporter-destination=junit.xml",
        guard,
    ]
    if (
        scripts != expected
        or proposed["pool"]["vmImage"] != "ubuntu-24.04"
        or setup["inputs"].get("version") != "26.13.0"
        or source_lint.get("continueOnError") is not True
        or "failTaskOnMissingResultsFile" in source_publisher["inputs"]
        or any(step.get("continueOnError", False) is not False for step in proposed["steps"] if "script" in step)
        or publisher.get("condition") != "succeededOrFailed()"
        or publisher["inputs"].get("testResultsFormat") != "JUnit"
        or publisher["inputs"].get("testResultsFiles") != "junit.xml"
        or any(
            publisher["inputs"].get(key) is not True
            for key in ("failTaskOnFailedTests", "failTaskOnMissingResultsFile", "failTaskOnFailureToPublishResults")
        )
    ):
        raise ValueError("YAML does not match the intended control contracts")

    node, npm = args.node.resolve(strict=True), args.npm_cli.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    fixture = output / "fixture"
    fixture.mkdir()
    manifest = {
        "name": "independent-native-test-fixture",
        "version": "1.0.0",
        "private": True,
        "scripts": {"test": "node --test", "lint": "node lint.cjs"},
    }
    (fixture / "package.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    (fixture / "lint.cjs").write_text(
        "if (process.env.FAIL_LINT) { console.error('fixture lint failure'); process.exit(23); }\n", encoding="utf-8"
    )
    (fixture / "sample.test.cjs").write_text(
        "const test = require('node:test');\nconst assert = require('node:assert/strict');\n"
        "test('fixture passes unless explicitly failed', () => assert.equal(process.env.FAIL_SAMPLE, undefined));\n",
        encoding="utf-8",
        newline="\n",
    )
    env = dict(os.environ)
    env["PATH"] = str(node.parent) + os.pathsep + env["PATH"]
    env["npm_config_userconfig"] = str(output / "empty-user.npmrc")
    env["npm_config_globalconfig"] = str(output / "empty-global.npmrc")
    env["npm_config_cache"] = str(output / "npm-cache")
    env["npm_config_offline"] = "true"
    env["npm_config_update_notifier"] = "false"
    env.pop("FAIL_SAMPLE", None)
    env.pop("FAIL_LINT", None)
    calls: dict[str, dict[str, object]] = {}

    def run(name: str, command: list[str], *, marker: str | None = None) -> subprocess.CompletedProcess[bytes]:
        selected = dict(env)
        if marker is not None:
            selected[marker] = "1"
        result = subprocess.run(
            [str(node), str(npm), *command],
            cwd=fixture,
            env=selected,
            capture_output=True,
            timeout=45,
            check=False,
        )
        (output / f"{name}.stdout").write_bytes(result.stdout)
        (output / f"{name}.stderr").write_bytes(result.stderr)
        calls[name] = {
            "arguments": command,
            "exit_code": result.returncode,
            "stdout_sha256": digest(result.stdout),
            "stderr_sha256": digest(result.stderr),
        }
        return result

    def run_guard(name: str) -> subprocess.CompletedProcess[bytes]:
        code = "\n".join(guard.splitlines()[1:-1])
        command = ["bash", "-c", guard] if platform.system() == "Linux" else [sys.executable, "-c", code]
        description = (
            ["bash", "-c", "<example shell guard>"]
            if platform.system() == "Linux"
            else ["python", "-c", "<example guard body>"]
        )
        observed = subprocess.run(command, cwd=fixture, env=env, capture_output=True, timeout=15, check=False)
        (output / f"{name}.stdout").write_bytes(observed.stdout)
        (output / f"{name}.stderr").write_bytes(observed.stderr)
        calls[name] = {
            "arguments": description,
            "exit_code": observed.returncode,
            "stdout_sha256": digest(observed.stdout),
            "stderr_sha256": digest(observed.stderr),
        }
        return observed

    node_version = subprocess.check_output([str(node), "--version"], text=True, timeout=15).strip()
    npm_version = subprocess.check_output(
        [str(node), str(npm), "--version"], cwd=fixture, env=env, text=True, timeout=15
    ).strip()
    guard_python = "python3" if platform.system() == "Linux" else sys.executable
    guard_python_version = subprocess.check_output([guard_python, "--version"], env=env, text=True, timeout=15).strip()
    preparation = run("prepare_lock", ["install", "--package-lock-only", "--ignore-scripts"])
    install = run("candidate_install", shlex.split(scripts[0])[1:])
    lint_pass = run("candidate_lint_pass", shlex.split(scripts[1])[1:])
    lint_fail = run("candidate_lint_fail", shlex.split(scripts[1])[1:], marker="FAIL_LINT")
    plain = run("plain_test", ["test"])
    original_test = run("original_test", shlex.split(source_test["script"])[1:])
    pass_test = run("candidate_test_pass", shlex.split(scripts[2])[1:])
    pass_xml = (fixture / "junit.xml").read_bytes()
    (output / "passing-junit.xml").write_bytes(pass_xml)
    pass_guard = run_guard("guard_pass")
    (fixture / "junit.xml").unlink()
    fail_test = run("candidate_test_fail", shlex.split(scripts[2])[1:], marker="FAIL_SAMPLE")
    fail_xml = (fixture / "junit.xml").read_bytes()
    (output / "failing-junit.xml").write_bytes(fail_xml)
    passing, failing = ET.fromstring(pass_xml), ET.fromstring(fail_xml)
    (fixture / "junit.xml").unlink()
    sample = fixture / "sample.test.cjs"
    saved = output / "saved-sample.test.cjs"
    sample.rename(saved)
    try:
        empty_test = run("candidate_test_empty", shlex.split(scripts[2])[1:])
        empty_xml = (fixture / "junit.xml").read_bytes()
        (output / "empty-junit.xml").write_bytes(empty_xml)
        empty_guard = run_guard("guard_empty")
    finally:
        saved.rename(sample)
    (fixture / "junit.xml").unlink()
    original_sample = sample.read_bytes()
    try:
        sample.write_text(
            "const test = require('node:test'); test('skipped', {skip: 'control'}, () => {});\n", encoding="utf-8"
        )
        skipped_test = run("candidate_test_skipped", shlex.split(scripts[2])[1:])
        skipped_xml = (fixture / "junit.xml").read_bytes()
        (output / "skipped-junit.xml").write_bytes(skipped_xml)
        skipped_guard = run_guard("guard_skipped")
    finally:
        sample.write_bytes(original_sample)
    empty, skipped = ET.fromstring(empty_xml), ET.fromstring(skipped_xml)
    if (
        any(
            item.returncode != 0
            for item in (preparation, install, lint_pass, plain, pass_test, pass_guard, empty_test, skipped_test)
        )
        or lint_fail.returncode != 23
        or original_test.returncode == 0
        or b"bad option: --coverage" not in original_test.stderr
        or fail_test.returncode == 0
        or not passing.findall(".//testcase")
        or passing.findall(".//failure")
        or not failing.findall(".//failure")
        or empty.findall(".//testcase")
        or not skipped.findall(".//testcase/skipped")
        or empty_guard.returncode == 0
        or skipped_guard.returncode == 0
    ):
        raise ValueError("At least one independently checked runtime observation differed")
    result = {
        "schema_version": 1,
        "kind": "local_component_control_not_agent_benchmark",
        "source_sha256": digest(source),
        "candidate_sha256": digest(candidate),
        "node_version": node_version,
        "npm_version": npm_version,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "guard_python_version": guard_python_version,
        "guard_execution": "example_bash_step" if platform.system() == "Linux" else "guard_body_directly",
        "source_node_version": original["variables"]["nodeVersion"],
        "source_image": original["pool"]["vmImage"],
        "source_lint_continue_on_error": source_lint["continueOnError"],
        "source_missing_result_setting_explicit": "failTaskOnMissingResultsFile" in source_publisher["inputs"],
        "candidate_lint_continue_on_error": lint.get("continueOnError", False),
        "candidate_missing_result_fails": publisher["inputs"]["failTaskOnMissingResultsFile"],
        "calls": calls,
        "fixture_sha256": {
            name: digest((fixture / name).read_bytes())
            for name in ["package.json", "package-lock.json", "lint.cjs", "sample.test.cjs"]
        },
        "junit": {
            "passing_sha256": digest(pass_xml),
            "failing_sha256": digest(fail_xml),
            "passing_testcases": len(passing.findall(".//testcase")),
            "failing_testcases": len(failing.findall(".//testcase")),
            "failures": len(failing.findall(".//failure")),
            "empty_sha256": digest(empty_xml),
            "empty_testcases": len(empty.findall(".//testcase")),
            "skipped_sha256": digest(skipped_xml),
            "skipped_testcases": len(skipped.findall(".//testcase/skipped")),
        },
        "azure_service_run": False,
        "model_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "ok": True,
                "node": node_version,
                "npm": npm_version,
                "source_test_exit": original_test.returncode,
                "candidate_test_exit": pass_test.returncode,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
