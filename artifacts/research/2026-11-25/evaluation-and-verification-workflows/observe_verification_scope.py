"""Observe the difference between syntax, a unit lane, and affected callers."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

node, tool_root, output = (Path(value).resolve() for value in sys.argv[1:])
output.mkdir(exist_ok=False)
WINDOWS = sys.platform == "win32"
PINS = {
    "win32": "86fc4785327db5f5c7558dc6156c543b433c313e813a222e088086222ab4afa6",
    "linux": "a7ec1b37e6ff9d187e4198c5b6df9a4eb1c74dd31804fb3bac55cc4ceca1ac01",
}
UNIT = b"""const test = require('node:test');
const assert = require('node:assert/strict');
const { parseWorkers } = require('./config.cjs');
test('fills in an omitted worker count', () => assert.equal(parseWorkers(undefined), 4));
"""
CALLER = b"""const test = require('node:test');
const assert = require('node:assert/strict');
const { planWork } = require('./service.cjs');
test('preserves a configured zero-worker pause', () => assert.equal(planWork({ workers: 0 }), 0));
"""
SERVICE = b"""const { parseWorkers } = require('./config.cjs');
exports.planWork = config => parseWorkers(config.workers);
"""

def digest(value):
    return hashlib.sha256(value).hexdigest()

def verify(condition, message):
    if not condition:
        raise ValueError(message)

verify(digest(node.read_bytes()) == PINS[sys.platform], "Node source binding changed")
if WINDOWS:
    sys.path.insert(0, str(tool_root))
    from _windows_trial_process import run_owned

with tempfile.TemporaryDirectory(prefix="ascb-scope-") as temporary:
    root = Path(temporary)
    env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC") if key in os.environ}
    env.update(PATH=str(node.parent), TEMP=str(root), TMP=str(root), HOME=str(root), USERPROFILE=str(root),
               CI="1", FORCE_COLOR="0")
    def invoke(label, args):
        command = [str(node), *args]
        stdout_path, stderr_path = (output / (label + "." + name + ".native") for name in ("stdout","stderr"))
        if WINDOWS:
            with open(os.devnull, "rb") as stdin, stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                record = run_owned(command, cwd=root, stdin=stdin, stdout=stdout, stderr=stderr,
                                   timeout=16, output_limit=32768, memory_limit=384 * 1024**2, process_limit=8,
                                   environment=env)
            verify(record["termination_reason"] is None and record["job_active_processes_after_cleanup"] == 0, "Owned node job did not finish")
            status = record["exit_code"]
        else:
            proc = subprocess.run(command, env=env, cwd=root, capture_output=True, check=False,
                                  stdin=subprocess.DEVNULL, timeout=16)
            verify(len(proc.stdout + proc.stderr) <= 32768, "Native output exceeded its budget")
            stdout_path.write_bytes(proc.stdout)
            stderr_path.write_bytes(proc.stderr)
            status = proc.returncode
        return status, stdout_path.read_bytes(), stderr_path.read_bytes()

    (root/"config.test.cjs").write_bytes(UNIT)
    (root/"consumer.test.cjs").write_bytes(CALLER)
    (root/"service.cjs").write_bytes(SERVICE)
    config = root/"config.cjs"
    status, identity, stderr = invoke("version", ["--version"])
    verify(status == 0 and identity.strip() == b"v24.22.3" and not stderr, "Wrong Node runtime")
    observations = {}
    for label, operator in (("defective", "||"), ("corrected", "??")):
        config.write_bytes(f"exports.parseWorkers = value => value {operator} 4;\n".encode())
        entries = {}
        for lane, args, expected, needle in (
            ("syntax", ["--check", "config.cjs"], 0, b""),
            ("unit", ["--test", "--test-reporter=tap", "config.test.cjs"], 0, b"ok 1 - fills in an omitted worker count"),
            ("caller", ["--test", "--test-reporter=tap", "consumer.test.cjs"], int(label == "defective"),
             (b"not ok 1 - " if label == "defective" else b"ok 1 - ") + b"preserves a configured zero-worker pause"),
        ):
            status, stdout, stderr = invoke(label+"-"+lane, args)
            verify(status == expected and needle in stdout, f"Wrong verification result under {label}/{lane}")
            if expected:
                verify(b"4 !== 0" in stdout, "A caller result supplied the wrong failure")
            if lane == "syntax":
                verify(not stdout and not stderr, "Syntax check returned unexpected output")
            entries[lane] = {"exit":status,"stdout_sha256":digest(stdout),"stderr_sha256":digest(stderr)}
        observations[label] = {"implementation_sha256":digest(config.read_bytes()),"lanes":entries}
report = {"runtime":"Node.js 24.22.3","platform":sys.platform,"machine":platform.machine(),
          "tests":{"unit_sha256":digest(UNIT),"caller_sha256":digest(CALLER),"service_sha256":digest(SERVICE)},
          "observations":observations,"owned_scratch_removed":not root.exists(),"model_attempts":0}
(output/"result.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps({"platform":sys.platform,"same_lanes_before_and_after":3,"owned_scratch_removed":not root.exists()}))
