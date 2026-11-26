"""Independent boundary-mutant control on a disposable Windows fixture."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir
from urllib.parse import urlparse

ROOT, EVIDENCE = (Path(value).resolve(strict=True) for value in sys.argv[1:])
sys.path.insert(0, str(ROOT / "tools"))

binding = json.loads((EVIDENCE / "windows-node.json").read_text(encoding="utf-8"))
version = json.loads((EVIDENCE / "stryker-core-release.native.json").read_bytes())["version"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(name, data):
    (EVIDENCE / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


node = Path(binding["node"]).resolve(strict=True)
npm = Path(binding["npm"]).resolve(strict=True)
assert sha(node.read_bytes()) == binding["nodeHash"]
assert sha(npm.read_bytes()) == binding["npmHash"]

# Freeze fail/kill expectations before the test runner observes any mutants.
source = b"export function price(cents) {\n  return cents >= 100 ? cents - 10 : cents;\n}\n"
minimal_tests = """import { test } from "node:test";
import assert from "node:assert/strict";
import { price } from "./price.mjs";
test("prices away from the cutoff", () => {
    assert.equal(price(90), 90);
    assert.equal(price(200), 190);
});
"""
boundary_test = """test("discount starts at the exact cutoff", () => {
    assert.equal(price(100), 90);
});
"""
save(
    "stryker-plan.json",
    {
        "tool": "@stryker-mutator/core",
        "version": version,
        "fixture": "integer retail discount starts at 100 cents",
        "change": {"line": 2, "operator": ">=", "replacement": ">"},
        "source_sha256": sha(source),
        "coarse_tests_sha256": sha(minimal_tests.encode()),
        "precise_tests_sha256": sha((minimal_tests + boundary_test).encode()),
        "expected": {"coarse": "Survived", "precise": "Killed", "invalid_baseline": "rejected"},
        "comparative_model_benchmark": False,
    },
)
temp_parent = Path(gettempdir()).resolve(strict=True)
evidence = {"schema_version": 1, "tool_identity": binding, "tool_version": version, "stages": {}}
with TemporaryDirectory(prefix="asl-mut-", dir=temp_parent) as temp:
    root = Path(temp).resolve(strict=True)
    assert root.parent == temp_parent and root.name.startswith("asl-mut-") and root != ROOT
    project, home, scratch, cache = (root / name for name in ("project", "home", "tmp", "cache"))
    for folder in (project, home, scratch, cache):
        folder.mkdir()
    user_config = home / "npmrc"
    global_config = home / "global-npmrc"
    user_config.write_bytes(b"")
    global_config.write_bytes(b"")
    env = {name: os.environ[name] for name in ("SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if name in os.environ}
    env.update(
        PATH=os.pathsep.join((str(node.parent), str(Path(env["SystemRoot"]) / "System32"))),
        HOME=str(home),
        USERPROFILE=str(home),
        APPDATA=str(home),
        LOCALAPPDATA=str(home),
        TEMP=str(scratch),
        TMP=str(scratch),
        npm_config_registry="https://registry.npmjs.org/",
        npm_config_userconfig=str(user_config),
        npm_config_globalconfig=str(global_config),
        npm_config_cache=str(cache),
        npm_config_update_notifier="false",
        npm_config_engine_strict="true",
    )

    def run(label, args, timeout=65, expected_exit=0):
        from _windows_trial_process import run_owned

        with (
            open(os.devnull, "rb") as stdin,
            (EVIDENCE / (label + ".stdout.native")).open("wb") as stdout,
            (EVIDENCE / (label + ".stderr.native")).open("wb") as stderr,
        ):
            process = run_owned(
                [str(node), *args],
                cwd=project,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                output_limit=1024**2,
                environment=env,
                memory_limit=768 * 1024**2,
                process_limit=12,
                write_io_limit=384 * 1024**2,
            )
        evidence["stages"][label] = process
        save("stryker-result.json", evidence)
        assert process["exit_code"] == expected_exit and process["termination_reason"] is None, (label, process)
        assert process["assigned_before_resume"] and process["job_active_processes_after_cleanup"] == 0

    (project / "package.json").write_text(
        json.dumps(
            {
                "name": "independent-volume-discount-fixture",
                "version": "1.0.0",
                "private": True,
                "type": "module",
                "devDependencies": {"@stryker-mutator/core": version},
            }
        ),
        encoding="utf-8",
    )
    run(
        "isolated-install",
        [str(npm), "install", "--ignore-scripts", "--no-fund", "--no-audit", "--package-lock"],
        timeout=100,
    )
    native_lock = (project / "package-lock.json").read_bytes()
    lock = json.loads(native_lock)
    for package, item in lock["packages"].items():
        if package:
            parsed = urlparse(item["resolved"])
            assert parsed.scheme == "https" and parsed.hostname == "registry.npmjs.org"
            assert item["integrity"].startswith("sha512-")
    assert lock["packages"]["node_modules/@stryker-mutator/core"]["version"] == version
    (EVIDENCE / "stryker-package-lock.native.json").write_bytes(native_lock)
    lock_sha = sha(native_lock)
    runner = str(project / "node_modules/@stryker-mutator/core/bin/stryker.js")
    config = project / "stryker.json"
    config.write_text(
        json.dumps(
            {
                "mutate": ["price.mjs"],
                "testRunner": "command",
                "commandRunner": {"command": "node --test price.test.mjs"},
                "coverageAnalysis": "off",
                "concurrency": 1,
                "timeoutMS": 5000,
                "reporters": ["json"],
                "jsonReporter": {"fileName": "mutations.json"},
                "cleanTempDir": True,
            }
        ),
        encoding="utf-8",
    )
    (project / "price.mjs").write_bytes(source)
    tests = project / "price.test.mjs"
    results = {}
    for label, testcase, expectation in (
        ("coarse", minimal_tests, "Survived"),
        ("precise", minimal_tests + boundary_test, "Killed"),
    ):
        tests.write_bytes(testcase.encode())
        report = project / "mutations.json"
        assert not report.exists()
        run(label + "-baseline", ["--test", "price.test.mjs"])
        run(label + "-campaign", [runner, "run", "stryker.json"])
        native = report.read_bytes()
        (EVIDENCE / (label + "-report.native.json")).write_bytes(native)
        result = json.loads(native)
        assert set(result["files"]) == {"price.mjs"}
        matches = [
            mutant
            for mutant in result["files"]["price.mjs"]["mutants"]
            if mutant["location"]["start"]["line"] == 2
            and source.decode()
            .splitlines()[1][mutant["location"]["start"]["column"] - 1 : mutant["location"]["end"]["column"] - 1]
            .strip()
            in {">=", "cents >= 100"}
            and mutant["replacement"].strip() in {">", "cents > 100"}
        ]
        assert len(matches) == 1, result["files"]["price.mjs"]["mutants"]
        assert matches[0]["status"] == expectation, matches[0]
        assert (project / "price.mjs").read_bytes() == source
        assert tests.read_bytes() == testcase.encode()
        assert sha((project / "package-lock.json").read_bytes()) == lock_sha
        results[label] = {"status": expectation, "report_sha256": sha(native), "mutant": matches[0]}
        report.unlink()

    # The original suite must pass before mutant results are eligible.
    invalid = (minimal_tests + boundary_test).replace("price(100), 90", "price(100), 100")
    tests.write_bytes(invalid.encode())
    run("invalid-baseline", ["--test", "price.test.mjs"], expected_exit=1)
    run("invalid-campaign", [runner, "run", "stryker.json"], expected_exit=1)
    assert not (project / "mutations.json").exists()
    assert (project / "price.mjs").read_bytes() == source
    assert tests.read_bytes() == invalid.encode()
    invalid_output = (EVIDENCE / "invalid-campaign.stdout.native").read_bytes()
    invalid_error = (EVIDENCE / "invalid-campaign.stderr.native").read_bytes()
    assert b"There were failed tests in the initial test run." in invalid_output + invalid_error
    results["invalid_baseline"] = {
        "status": "rejected",
        "report_sha256": None,
        "diagnostics_sha256": sha(invalid_output + invalid_error),
    }

assert not root.exists()
evidence.update({"outcomes": results, "package_lock_sha256": lock_sha, "temporary_root_removed": True})
save("stryker-result.json", evidence)
print(
    json.dumps(
        {
            "outcomes": {name: outcome["status"] for name, outcome in results.items()},
            "jobs_closed": len(evidence["stages"]),
        }
    )
)
