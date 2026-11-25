"""Observe actual Playwright Test fixture setup, execution, and teardown."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

node, tool_root, source, output, mode = map(Path, sys.argv[1:])
source = source.resolve(strict=True)
output.mkdir(exist_ok=False)
output = output.resolve(strict=True)
node = node.resolve(strict=True)
tool_root = tool_root.resolve(strict=True)
packages = {"@playwright/test": "playwright-test-latest", "playwright": "playwright", "playwright-core": "playwright-core"}
version = "1.65.1"
fixture_path = source / "playwright-fixture.spec.cjs"
archives = source / "playwright-locked-archives"
known_node = {
    "win32": "86fc4785327db5f5c7558dc6156c543b433c313e813a222e088086222ab4afa6",
    "linux": "a7ec1b37e6ff9d187e4198c5b6df9a4eb1c74dd31804fb3bac55cc4ceca1ac01",
}

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def package_file(name, filename, dependencies):
    source_bytes = (source / (filename + ".native.json")).read_bytes()
    metadata = json.loads(source_bytes)
    require(metadata["name"] == name and metadata["version"] == version, "Unexpected Playwright release metadata")
    require(metadata.get("dependencies", {}) == dependencies, "Unexpected required runtime graph")
    url = metadata["dist"]["tarball"]
    parsed = urllib.parse.urlsplit(url)
    require(parsed.scheme == "https" and parsed.netloc == "registry.npmjs.org", "Unexpected native package origin")
    artifact = archives / (filename + ".tgz")
    if str(mode) == "fetch":
        with urllib.request.urlopen(url, timeout=20) as download:
            raw = download.read(20 * 1024**2 + 1)
    else:
        raw = artifact.read_bytes()
    sri = "sha512-" + base64.b64encode(hashlib.sha512(raw).digest()).decode()
    require(0 < len(raw) <= 20 * 1024**2 and sri == metadata["dist"]["integrity"], "Native package archive drift")
    if str(mode) == "fetch":
        with artifact.open("xb") as stream:
            stream.write(raw)
    return artifact, {"sha512": sri, "metadata_sha256": digest(source_bytes), "compressed_bytes": len(raw)}

def extract(archive, directory):
    directory.mkdir(parents=True)
    with tarfile.open(archive) as payload:
        files = []
        for item in payload:
            parts = PurePosixPath(item.name)
            require(
                parts.parts and parts.parts[0] == "package" and len(parts.parts) > 1
                and not parts.is_absolute() and ".." not in parts.parts and (item.isdir() or item.isfile()),
                "An unexpected package member is outside the reviewed layout",
            )
            files.append(item.replace(name=PurePosixPath(*parts.parts[1:]).as_posix()))
        payload.extractall(directory, members=files, filter="data")

def capture(args, directory, env, label):
    stdout_path, stderr_path = (output / f"{label}.{name}.native" for name in ("stdout", "stderr"))
    if sys.platform == "win32":
        sys.path.insert(0, str(tool_root))
        from _windows_trial_process import run_owned
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr, open(os.devnull, "rb") as stdin:
            receipt = run_owned([str(node), *args], cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr,
                                timeout=28, output_limit=512 * 1024, memory_limit=512 * 1024**2, process_limit=10,
                                environment=env)
        require(receipt["termination_reason"] is None and receipt["job_active_processes_after_cleanup"] == 0,
                "Playwright's process or job failed")
        status, process = receipt["exit_code"], receipt
    else:
        result = subprocess.run([str(node), *args], cwd=directory, env=env, timeout=27, check=False,
                                stdin=subprocess.DEVNULL, capture_output=True)
        require(len(result.stdout + result.stderr) <= 512 * 1024, "Native output exceeded its byte budget")
        stdout_path.write_bytes(result.stdout)
        stderr_path.write_bytes(result.stderr)
        status, process = result.returncode, {}
    return status, stdout_path.read_bytes(), stderr_path.read_bytes(), process

require(str(mode) in {"fetch", "replay"}, "Use a declared package acquisition or replay mode")
require(sys.platform in known_node and digest(node.read_bytes()) == known_node[sys.platform], "Unexpected Node executable")
if str(mode) == "fetch":
    archives.mkdir()
with tempfile.TemporaryDirectory(prefix="ascb-pw-") as temporary:
    root = Path(temporary)
    npm_inputs = {}
    for (name, filename), dependencies in zip(packages.items(), ({"playwright": version}, {"playwright-core": version}, {}), strict=True):
        package, npm_inputs[name] = package_file(name, filename, dependencies)
        extract(package, root / "node_modules" / name)
    cli = root / "node_modules" / "@playwright/test/cli.js"
    require(cli.is_file(), "Publisher's test command missing")
    test_directory = root / "cases"
    test_directory.mkdir()
    target = test_directory / fixture_path.name
    shutil.copyfile(fixture_path, target)
    (root / "playwright.config.cjs").write_text(
        'module.exports = { testDir: "./cases", workers: 1, retries: 0, timeout: 5000,'
        'globalTimeout: 15000, reporter: "json", outputDir: "./trial-output" };\n',
        encoding="utf-8", newline="\n",
    )
    env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC") if key in os.environ}
    env.update(PATH=str(node.parent), TEMP=str(root), TMP=str(root), TMPDIR=str(root),
               HOME=str(root), USERPROFILE=str(root), LOCALAPPDATA=str(root), APPDATA=str(root),
               CI="1", FORCE_COLOR="0", PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD="1")
    code, version_out, errors, _ = capture(["--version"], root, env, "version")
    require(code == 0 and version_out.strip() == b"v24.22.3" and not errors, "Unexpected Node version outcome")
    code, version_out, errors, _ = capture([str(cli), "--version"], root, env, "playwright-version")
    require(code == 0 and version_out.strip() == b"Version 1.65.1" and not errors, "Unexpected Playwright test runner")
    records = {}
    for label, stage, cleanup, exit_code, expected_body, expected_leftover, expected_error in (
        ("success", "ready", "registered", 0, True, False, ""),
        ("setup-error-released", "setup", "registered", 1, False, False, "deliberate second acquisition failure"),
        ("body-failure-released", "body", "registered", 1, True, False, "intended behavior assertion"),
        ("setup-error-leaked", "setup", "missing-finally", 1, False, True, "deliberate second acquisition failure"),
    ):
        parent = root / label
        parent.mkdir()
        case_env = env | {"CONTROL_PARENT": str(parent), "CONTROL_STAGE": stage, "CONTROL_MODE": cleanup}
        status, stdout, stderr, process = capture([str(cli), "test", "--config", str(root / "playwright.config.cjs")],
                                                   root, case_env, label)
        report = json.loads(stdout)
        specs = [spec for suite in report["suites"] for spec in suite["specs"]]
        require(len(specs) == 1 and specs[0]["title"] == "uses the resource and records its state", f"Wrong case under {label}")
        [execution] = specs[0]["tests"]
        [attempt] = execution["results"]
        require(status == exit_code, f"Unexpected native exit under {label}")
        require(attempt["status"] == ("failed" if exit_code else "passed"), f"Unexpected outcome under {label}")
        if expected_error:
            require(any(err.get("message", "").splitlines()[:1] == ["Error: " + expected_error] for err in attempt["errors"]),
                    f"Wrong reported failure under {label}")
        require((parent / "body-entered.txt").is_file() is expected_body, f"Wrong test execution phase under {label}")
        [name] = (parent / "allocation.txt").read_text(encoding="utf-8").splitlines()
        require(Path(name).name == name and name.startswith("owned-"), f"Unexpected allocation under {label}")
        require((parent / name).exists() is expected_leftover, f"Wrong cleanup observation under {label}")
        records[label] = {"exit": status, "test_outcome": attempt["status"], "test_body_ran": expected_body,
                         "expected_failure_diagnostic": expected_error, "resource_remained_before_scratch_cleanup": expected_leftover,
                         "stdout_sha256": digest(stdout), "stderr_sha256": digest(stderr),
                         "owned_processes_after": process.get("job_active_processes_after_cleanup")}
results = {"playwright_test": version, "node": "24.22.3", "platform": sys.platform, "machine": platform.machine(),
           "fixture_sha256": digest(fixture_path.read_bytes()), "packages": npm_inputs, "controls": records,
           "owned_scratch_removed": not root.exists(), "model_attempts": 0}
(output / "result.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"platform": sys.platform, "controls": len(records), "scratch_removed": not root.exists()}))
