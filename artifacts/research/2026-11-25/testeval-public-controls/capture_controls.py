"""Capture TestEval publisher and independent pytest results for frozen controls."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

INPUT = Path("/input")
CONTROL = Path("/control")
OUTPUT = Path("/output")
CASES = Path("/tmp/testeval")
CASE_NAME = "test_control"

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def capture(label, argv, cwd):
    out = OUTPUT / f"{label}.stdout.native"
    err = OUTPUT / f"{label}.stderr.native"
    with out.open("xb") as stdout, err.open("xb") as stderr:
        result = subprocess.run(
            argv, cwd=cwd, env=ENV, stdin=subprocess.DEVNULL,
            stdout=stdout, stderr=stderr, timeout=24, check=False,
        )
    return result.returncode

frame_path = INPUT / "frame.json"
frame = json.loads(frame_path.read_bytes())
spec_path = CONTROL / "testeval-assertion-controls.json"
spec = json.loads(spec_path.read_bytes())
require(spec["schema_version"] == 1 and spec["model_attempts"] == frame["model_attempts"] == 0, "Unsupported control experiment")
require(digest(frame_path) == spec["source_frame_sha256"] == "0180237d062210a351ef5c6ef14ab6e39dbba339f3f98c50af59313e811a7762", "Source frame drift")
require(digest(INPUT / "eval_overall.py") == frame["publisher_evaluator_sha256"], "Publisher evaluator drift")
data_path = INPUT / "selected.jsonl"
require(digest(data_path) == "d77e5dbaa3939903c54d1e6f887a3fc8876730293143f88d8ef00f538c64b232", "Publisher projection drift")
records = {row["task_num"]: row for row in map(json.loads, data_path.read_bytes().splitlines())}
expected_cases = {(next(row["task_num"] for row in frame["cases"] if row["publisher_difficulty"] == level), level) for level in (1, 2, 3)}
require(len(spec["cases"]) == 3 and {(row["task_num"], row["difficulty"]) for row in spec["cases"]} == expected_cases, "Outside the declared public calibration frame")
CASES.mkdir()
ENV = {
    "PATH": "/runtime/venv/bin:/usr/bin:/bin", "HOME": str(CASES),
    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1",
    "LANG": "C.UTF-8",
}

reports = []
for row in spec["cases"]:
    task_id = row["task_num"]
    record = records[task_id]
    require(record.keys() == {"task_num", "difficulty", "func_name", "code"}, "The input must project the code under test only")
    function = record["func_name"]
    require(function.isidentifier() and record["difficulty"] == row["difficulty"], "Unexpected published target")
    portable = f"def {CASE_NAME}():\n    observed = Solution().{function}({row['input']!r})\n"
    publisher_case = f"test_{function}"
    publisher = (
        f"def {publisher_case}():\n    solution = Solution()\n"
        f"    observed = solution.{function}({row['input']!r})\n"
    )
    matching = f"    assert observed == {row['expected']!r}, 'independent behavior contract'\n"
    mismatching = f"    assert observed == {row['intended_false']!r}, 'independent behavior contract'\n"
    for condition, pytest_case, test_body in (
        ("matching-portable-shape", CASE_NAME, portable + matching),
        ("mismatching-portable-shape", CASE_NAME, portable + mismatching),
        ("matching", publisher_case, publisher + matching),
        ("mismatching", publisher_case, publisher + mismatching),
        ("no-call", publisher_case, f"def {publisher_case}():\n    assert True\n"),
    ):
        label = f"task-{task_id}-{condition}"
        case_root = CASES / label
        predictions = case_root / "predictions"
        independent = case_root / "independent"
        predictions.mkdir(parents=True)
        independent.mkdir()
        for filename in (".coveragerc", "eval_overall.py", "data_utils.py"):
            shutil.copyfile(INPUT / filename, case_root / filename)
        payload = {**record, "tests": [test_body]}
        (predictions / "control.jsonl").write_text(json.dumps(payload) + "\n", encoding="utf-8")
        program = independent / "under_test.py"
        program.write_bytes(record["code"].encode())
        pytest_input = independent / "test_control.py"
        pytest_input.write_text("from under_test import Solution\n\n" + test_body, encoding="utf-8")
        (OUTPUT / (label + ".fixture.py")).write_bytes(pytest_input.read_bytes())
        publisher = capture(label + "-publisher", [sys.executable, "eval_overall.py", "--path", "control.jsonl", "--ks", "1"], case_root)
        junit = OUTPUT / (label + ".junit.xml")
        pytest = capture(label + "-pytest", [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                             f"--junitxml={junit}", "test_control.py"], independent)
        (OUTPUT / (label + ".exit.txt")).write_text(f"{pytest}\n", encoding="utf-8")
        reports.append({"label": label, "task_id": task_id, "difficulty": row["difficulty"],
                        "condition": condition, "function": function, "pytest_case": pytest_case, "program_sha256": digest(program),
                        "publisher_exit": publisher, "pytest_exit": pytest})
(OUTPUT / "capture.json").write_text(json.dumps({
    "source_frame_sha256": digest(frame_path), "control_specification_sha256": digest(spec_path),
    "publisher_evaluator_sha256": digest(INPUT / "eval_overall.py"),
    "python": sys.version.split()[0], "capture_sha256": digest(Path(__file__)),
    "records": reports, "model_attempts": 0,
}, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"publisher_and_independent_pairs": len(reports),
                  "nonzero_publisher_exits": sum(row["publisher_exit"] != 0 for row in reports),
                  "model_attempts": 0}))
