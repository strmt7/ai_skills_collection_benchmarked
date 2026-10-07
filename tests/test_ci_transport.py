from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_trial_protocol_survives_lf_git_transport(tmp_path):
    relative = "benchmarks/agent-effectiveness/development/protocol-v2.json"
    original = (ROOT / relative).read_bytes()
    attempt = json.loads(
        (ROOT / "artifacts/agent-trials/development-v2/repetition-1/default/result.json").read_text(encoding="utf-8")
    )
    assert hashlib.sha256(original).hexdigest() == attempt["protocol_sha256"]
    source = tmp_path / "source"
    source.mkdir()
    (source / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes())
    protocol = source / relative
    protocol.parent.mkdir(parents=True)
    protocol.write_bytes(original)

    def git(*arguments, cwd=source):
        return subprocess.check_output(
            ["git", "-c", "core.longpaths=true", "-c", "core.autocrlf=false", *arguments],
            cwd=cwd,
            stderr=subprocess.PIPE,
        )

    git("init", "--initial-branch=main")
    git("add", ".gitattributes", relative)
    git("-c", "user.name=AI agent", "-c", "user.email=", "commit", "-m", "Qualify frozen protocol transport")
    clone = tmp_path / "clone"
    git("clone", "--no-local", str(source), str(clone))
    assert (clone / relative).read_bytes() == original


def test_windows_jobs_enable_long_paths_before_checkout():
    jobs = []
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        for job in yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs", {}).values():
            matrix = job.get("strategy", {}).get("matrix", {})
            platforms = [job.get("runs-on"), *matrix.get("os", [])]
            platforms.extend(item.get("os") for item in matrix.get("include", []))
            if any(isinstance(platform, str) and "windows" in platform for platform in platforms):
                jobs.append(job)
                environment = job["env"]
                assert environment["GIT_CONFIG_COUNT"] == "1"
                assert environment["GIT_CONFIG_KEY_0"] == "core.longpaths"
                assert environment["GIT_CONFIG_VALUE_0"] == "true"
    assert jobs


def test_scanner_runtime_lock_matches_verified_development_release():
    runtime = (ROOT / "requirements-runtime-lock.txt").read_text(encoding="utf-8")
    development = (ROOT / "requirements-lock.txt").read_text(encoding="utf-8")
    requirement = runtime[runtime.index("pyyaml==") :].strip()
    assert requirement in development
    assert "--hash=sha256:" in requirement
    workflow = yaml.safe_load((ROOT / ".github/workflows/secret-scan.yml").read_text(encoding="utf-8"))
    commands = [step.get("run", "") for step in workflow["jobs"]["secret-scan"]["steps"]]
    install = "python -m pip install --require-hashes --no-deps -r requirements-runtime-lock.txt"
    scan = "python3 tools/check_no_secret_patterns.py --history"
    assert commands.index(install) < commands.index(scan)
