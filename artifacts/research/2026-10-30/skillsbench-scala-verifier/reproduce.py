"""Reproduce a pinned development verifier's handling of test exit codes."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

INPUTS = {
    "verifier": "fc4e797cb49906159fcbb204b24553984e5a800bc0f5df1534a02393d5c1b177",
    "workspace_source": "180a9aaa519b759e30c595399a94ce3f1d25dd54b2ac9f5475df38cb786ecf51",
    "reference_source": "962e79378766345f9acc49b11e8bbe3219021c532f69e0a78824327e53859e3e",
    "dockerfile": "2e83a1622dd5649d214c029af925066044bf4191015d7c97489955246f70bef5",
}
EXTRA_IMPORT = b"import scala.language.implicitConversions\n"


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def run_case(
    module, source: Path, root: Path, compile_exit: int, test_exit: int, test_output: str
) -> dict[str, object]:
    candidate = root / "candidate.scala"
    shutil.copyfile(source, candidate)
    build = root / "build.sbt"
    build.write_text('name := "control"\n', encoding="utf-8")
    test = root / "TokenizerSpec.scala"
    test.write_text("// control placeholder\n", encoding="utf-8")
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args[1])
        if args[1] == "compile":
            out = "compiled" if compile_exit == 0 else "[error] simulated compile failure"
            return subprocess.CompletedProcess(args, compile_exit, stdout=out, stderr="")
        if args[1] == "test":
            return subprocess.CompletedProcess(args, test_exit, stdout=test_output, stderr="")
        raise RuntimeError(f"Unexpected command: {args}")

    evaluator = module.ScalaTokenizerEvaluator(str(candidate), str(build), str(test), str(root / "project"))
    with (
        patch.object(module.shutil, "which", return_value="synthetic-sbt"),
        patch.object(module.subprocess, "run", side_effect=fake_run),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        result = evaluator.run_full_evaluation()
    return {
        "calls": calls,
        "simulated_compile_exit": compile_exit,
        "simulated_test_exit": test_exit if "test" in calls else None,
        "reported_passed": result["passed"],
        "reported_compilation": result["compilation"],
        "reported_tests": result["tests"],
        "overall_score": result["overall_score"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--workspace-source", type=Path, required=True)
    parser.add_argument("--reference-source", type=Path, required=True)
    parser.add_argument("--dockerfile", type=Path, required=True)
    args = parser.parse_args()
    data = {key: pinned(getattr(args, key), digest) for key, digest in INPUTS.items()}
    if data["workspace_source"].count(EXTRA_IMPORT) != 1:
        raise ValueError("Expected workspace import differs")
    if data["workspace_source"].replace(EXTRA_IMPORT, b"", 1) != data["reference_source"]:
        raise ValueError("The two source files no longer match after removing the import")
    if b"COPY localtest /root/localtest" not in data["dockerfile"]:
        raise ValueError("The workspace copy instruction changed")
    spec = importlib.util.spec_from_file_location("skillsbench_scala_dev_verifier", args.verifier)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load the pinned verifier")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    temp_root = Path(tempfile.gettempdir()).resolve()
    cases = {}
    definitions = (
        ("success", 0, 0, "10 tests succeeded\n0 tests failed\n"),
        ("nonzero_test_exit", 0, 1, "10 tests succeeded\n0 tests failed\n"),
        ("reported_test_failure", 0, 0, "9 tests succeeded\n1 test failed\n"),
        ("compile_failure", 1, 0, "10 tests succeeded\n0 tests failed\n"),
    )
    for name, compile_exit, test_exit, output in definitions:
        with tempfile.TemporaryDirectory(prefix="skillsbench-verifier-control-", dir=temp_root) as tmp:
            case_root = Path(tmp).resolve()
            if not case_root.is_relative_to(temp_root):
                raise ValueError("Unexpected temporary path")
            cases[name] = run_case(module, args.workspace_source, case_root, compile_exit, test_exit, output)
    expected = {"success": True, "nonzero_test_exit": True, "reported_test_failure": False, "compile_failure": False}
    if {name: case["reported_passed"] for name, case in cases.items()} != expected:
        raise AssertionError("Pinned verifier outcomes changed")
    if cases["nonzero_test_exit"]["simulated_test_exit"] != 1:
        raise AssertionError("The nonzero exit control did not execute")
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "input_sha256": INPUTS,
                "workspace_copy_matches_reference_except_import": True,
                "all_compiler_and_test_commands_simulated": True,
                "cases": cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
