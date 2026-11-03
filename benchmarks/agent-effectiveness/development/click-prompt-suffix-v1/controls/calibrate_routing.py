"""Calibrate trusted Click variants against stdout/stderr prompt contracts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONTROLS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("terminal_calibration", CONTROLS / "calibrate_terminal.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Terminal calibration is unavailable")
terminal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(terminal)
calibrate = terminal.calibrate

ROUTING_CASES = [
    "test_confirm_to_stderr",
    "test_confirm_to_stdout",
    "test_prompt_to_stderr",
    "test_prompt_to_stdout",
]
STDERR_CASES = {"test_confirm_to_stderr", "test_prompt_to_stderr"}
EXPECTED_FAILURES = {
    "upstream": set(),
    "no-workaround": set(),
    "entire-input-prompt": STDERR_CASES,
    "err-ignored": STDERR_CASES,
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_variant(root: Path, name: str, patch: bytes) -> None:
    terminal.apply_variant(root, "upstream" if name == "err-ignored" else name, patch)
    if name != "err-ignored":
        return
    target = root / "src/click/termui.py"
    data = target.read_bytes()
    for before, after in (
        (b"echo(text[:-1], nl=False, err=err)", b"echo(text[:-1], nl=False, err=False)"),
        (b"echo(prompt[:-1], nl=False, err=err)", b"echo(prompt[:-1], nl=False, err=False)"),
    ):
        if data.count(before) != 1:
            raise ValueError("Unexpected pinned source for err-ignored variant")
        data = data.replace(before, after)
    target.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target-python", type=Path, default=Path(sys.executable))
    args = parser.parse_args(argv)
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output.is_relative_to(source):
        raise ValueError("Output must be outside the source tree")
    before = calibrate.verify_source(source)
    inputs = {
        str(path.relative_to(CONTROLS.parent)): digest(path.read_bytes())
        for path in (
            Path(__file__).resolve(),
            CONTROLS / "test_routing_contract.py",
            CONTROLS / "calibrate_terminal.py",
            CONTROLS / "calibrate.py",
            CONTROLS / "test_contract.py",
            CONTROLS / "upstream-patch.json",
            CONTROLS.parent / "cases.json",
            CONTROLS.parent / "source.json",
            CONTROLS.parent / "tree.json",
        )
    }
    patch = calibrate.upstream_patch()
    if digest(patch) != calibrate.PATCH_SHA256:
        raise ValueError("Upstream patch differs from its pin")
    python = args.target_python.resolve(strict=True)
    runtime = json.loads(
        subprocess.check_output(
            [
                str(python),
                "-I",
                "-c",
                "import json,platform,sys; print(json.dumps({'python':sys.version,'platform':platform.platform()}))",
            ],
            timeout=30,
        )
    )
    runtime["executable_sha256"] = digest(python.read_bytes())
    simulated_cases = json.loads((CONTROLS.parent / "cases.json").read_text(encoding="utf-8"))["cases"]
    if len(simulated_cases) != 16 or len(set(simulated_cases)) != 16:
        raise ValueError("Invalid simulated-case manifest")
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with tempfile.TemporaryDirectory(prefix="click-routing-") as temp:
        for name, expected in EXPECTED_FAILURES.items():
            root = Path(temp) / name
            shutil.copytree(source / "src", root / "src")
            apply_variant(root, name, patch)
            variant_before = calibrate.snapshot(root / "src")
            environment = dict(os.environ, CLICK_CONTROL_SOURCE=str(root / "src"))
            observations = {}
            for suite, script, cases, failures in (
                ("simulated", "test_contract.py", simulated_cases, set()),
                ("routing", "test_routing_contract.py", ROUTING_CASES, expected),
            ):
                # Preserve exact script bytes while giving tracebacks a portable filename.
                driver = (
                    "import pathlib,sys; p=pathlib.Path(sys.argv[1]); sys.argv=sys.argv[:1]; "
                    "ns=sys.modules['__main__'].__dict__; ns['__file__']=str(p); "
                    "exec(compile(p.read_bytes(),str(p),'exec'),ns)"
                )
                process = subprocess.run(
                    [str(python), "-I", "-B", "-X", "utf8", "-c", driver, script],
                    cwd=CONTROLS,
                    env=environment,
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
                (output / f"{name}-{suite}.stdout").write_bytes(process.stdout)
                (output / f"{name}-{suite}.stderr").write_bytes(process.stderr)
                observed = calibrate.verify_results(process.stderr, cases, failures, process.returncode)
                if failures and process.stderr.decode("utf-8").count(
                    "AssertionError: 'Question' not found in ''"
                ) != len(failures):
                    raise ValueError("Routing failures did not establish the expected missing prompt")
                observations[suite] = {
                    "failed_cases": observed,
                    "case_count": len(cases),
                    "exit_code": process.returncode,
                    "stdout_sha256": digest(process.stdout),
                    "stderr_sha256": digest(process.stderr),
                }
            if calibrate.snapshot(root / "src") != variant_before:
                raise ValueError("A trusted variant changed during qualification")
            results[name] = {
                "module_sha256": digest((root / "src/click/termui.py").read_bytes()),
                "suites": observations,
            }
    if calibrate.verify_source(source) != before:
        raise ValueError("Source changed during qualification")
    if inputs != {name: digest((CONTROLS.parent / name).read_bytes()) for name in inputs}:
        raise ValueError("Control inputs changed during qualification")
    result = {
        "schema_version": 1,
        "scope": "Trusted Click output-routing controls only; not an agent trial or a confined grader.",
        "source_commit": calibrate.COMMIT,
        "source_file_count": len(before),
        "source_snapshot_sha256": digest(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()),
        "runtime": runtime,
        "control_inputs_sha256": inputs,
        "variants": results,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
