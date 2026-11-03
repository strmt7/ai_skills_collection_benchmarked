"""Exercise trusted Click variants in a real POSIX terminal with readline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

CONTROLS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("click_calibration", CONTROLS / "calibrate.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Click source verifier is unavailable")
calibrate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calibrate)

PROGRAM = """
import pathlib, sys
sys.path.insert(0, sys.argv[1])
import readline, click
if not pathlib.Path(click.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[1]).resolve()):
    raise RuntimeError('unexpected Click source')
kind = sys.argv[2]
value = getattr(click, kind)('Question', prompt_suffix=': ', show_default=False)
print('RESULT=' + str(value))
"""


class CaseResult(TypedDict):
    passed: bool
    lines: list[str]
    trace: str
    sha256: str


class VariantResult(TypedDict):
    module_sha256: str
    simulated_cases: int
    simulated_stdout_sha256: str
    simulated_stderr_sha256: str
    cases: dict[str, CaseResult]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def terminal_lines(data: bytes) -> list[str]:
    """Interpret the bounded ASCII/VT sequences observed in the terminal cases."""
    line: list[str] = []
    lines: list[str] = []
    cursor = 0
    index = 0
    while index < len(data):
        char = data[index]
        if char == 27 and data[index : index + 2] == b"\x1b[":
            end = index + 2
            while end < len(data) and 48 <= data[end] <= 57:
                end += 1
            if end >= len(data):
                raise ValueError("Incomplete terminal control sequence")
            parameter = data[index + 2 : end]
            value = int(parameter) if parameter else 0
            operation = data[end]
            if operation == ord("G") and value >= 1:
                cursor = value - 1
            elif operation == ord("K") and value == 0:
                del line[cursor:]
            else:
                raise ValueError(f"Unsupported terminal control: {data[index : end + 1]!r}")
            index = end
        elif char == 13:
            cursor = 0
        elif char == 10:
            lines.append("".join(line))
            line = []
            cursor = 0
        elif char == 8:
            cursor = max(0, cursor - 1)
        elif char == 7:
            pass
        elif 32 <= char <= 126:
            while len(line) <= cursor:
                line.append(" ")
            line[cursor] = chr(char)
            cursor += 1
        else:
            raise ValueError(f"Unsupported terminal byte: {char}")
        index += 1
    if line:
        lines.append("".join(line))
    return lines


def read_until(fd: int, predicate: Callable[[bytes], bool], timeout: float = 10) -> bytes:
    result = b""
    deadline = time.monotonic() + timeout
    while not predicate(result):
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            raise TimeoutError("Terminal did not reach the expected state")
        try:
            chunk = os.read(fd, 4096)
        except OSError as exc:
            raise RuntimeError("Terminal closed before the expected state") from exc
        if not chunk:
            raise RuntimeError("Terminal closed before the expected state")
        result += chunk
        if len(result) > 65536:
            raise ValueError("Terminal output exceeded the control limit")
    return result


def terminal_case(python: Path, source: Path, kind: str, env: dict[str, str]) -> tuple[bytes, list[str]]:
    master, slave = importlib.import_module("pty").openpty()
    process: subprocess.Popen[bytes] | None = None
    try:
        fcntl = importlib.import_module("fcntl")
        termios = importlib.import_module("termios")
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
        process = subprocess.Popen(
            [str(python), "-I", "-B", "-X", "utf8", "-c", PROGRAM, str(source), kind],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=env,
            close_fds=True,
        )
        os.close(slave)
        slave = -1
        trace = read_until(master, lambda data: data.endswith(b"Question: "))
        os.write(master, b"abc")
        trace += read_until(master, lambda data: data.endswith(b"abc"))
        for _ in range(3):
            os.write(master, b"\x7f")
            trace += read_until(master, bool)
        answer = b"z" if kind == "prompt" else b"y"
        os.write(master, answer + b"\n")
        expected_result = b"RESULT=z\r\n" if kind == "prompt" else b"RESULT=True\r\n"
        trace += read_until(master, lambda data: expected_result in data)
        if process.wait(timeout=10) != 0:
            raise RuntimeError("Terminal child exited unsuccessfully")
        return trace, terminal_lines(trace)
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()
        if slave >= 0:
            os.close(slave)
        os.close(master)


def apply_variant(root: Path, name: str, patch: bytes) -> None:
    subprocess.run(["git", "-c", "core.autocrlf=false", "apply", "-"], cwd=root, input=patch, check=True, timeout=30)
    target = root / "src/click/termui.py"
    data = target.read_bytes()
    if digest(data) != calibrate.FIXED_SHA256:
        raise ValueError("Upstream patch does not match the pinned source")
    if name == "upstream":
        return
    if name == "no-workaround":
        replacements = [
            (b"echo(text[:-1], nl=False, err=err)", b"echo(text, nl=False, err=err)"),
            (b"return f(text[-1:])", b'return f("")'),
            (b"echo(prompt[:-1], nl=False, err=err)", b"echo(prompt, nl=False, err=err)"),
            (
                b"value = visible_prompt_func(prompt[-1:]).lower().strip()",
                b'value = visible_prompt_func("").lower().strip()',
            ),
        ]
    elif name == "entire-input-prompt":
        replacements = [
            (b"echo(text[:-1], nl=False, err=err)", b'echo("", nl=False, err=err)'),
            (b"return f(text[-1:])", b"return f(text)"),
            (b"echo(prompt[:-1], nl=False, err=err)", b'echo("", nl=False, err=err)'),
            (
                b"value = visible_prompt_func(prompt[-1:]).lower().strip()",
                b"value = visible_prompt_func(prompt).lower().strip()",
            ),
        ]
    else:
        raise ValueError(f"Unknown variant: {name}")
    for before, after in replacements:
        if data.count(before) != 1:
            raise ValueError(f"Unexpected source in {name}")
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
            CONTROLS / "calibrate.py",
            CONTROLS / "upstream-patch.json",
            CONTROLS / "test_contract.py",
            CONTROLS.parent / "tree.json",
            CONTROLS.parent / "source.json",
            CONTROLS.parent / "cases.json",
        )
    }
    patch = calibrate.upstream_patch()
    if digest(patch) != calibrate.PATCH_SHA256:
        raise ValueError("Upstream patch differs from its pin")
    python = args.target_python.resolve(strict=True)
    env = dict(os.environ, INPUTRC=os.devnull, TERM="xterm", LC_ALL="C.UTF-8")
    runtime = json.loads(
        subprocess.check_output(
            [
                str(python),
                "-I",
                "-c",
                "import json,platform,readline,sys; print(json.dumps({'python':sys.version,'platform':platform.platform(),'readline_backend':getattr(readline,'backend',None),'readline_doc':readline.__doc__,'readline_version':getattr(readline,'_READLINE_VERSION',None)}))",
            ],
            env=env,
            timeout=30,
        )
    )
    runtime["executable_sha256"] = digest(python.read_bytes())
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((CONTROLS.parent / "cases.json").read_text(encoding="utf-8"))
    cases = manifest["cases"]
    if manifest["schema_version"] != 1 or len(cases) != 16 or len(set(cases)) != 16:
        raise ValueError("Invalid simulated-case manifest")
    variants: dict[str, VariantResult] = {}
    with tempfile.TemporaryDirectory(prefix="click-terminal-") as temp:
        for name in ("upstream", "no-workaround", "entire-input-prompt"):
            root = Path(temp) / name
            shutil.copytree(source / "src", root / "src")
            apply_variant(root, name, patch)
            variant_before = calibrate.snapshot(root / "src")
            simulated_env = dict(env, CLICK_CONTROL_SOURCE=str(root / "src"))
            simulated = subprocess.run(
                [str(python), "-I", "-B", "-X", "utf8", str(CONTROLS / "test_contract.py")],
                env=simulated_env,
                capture_output=True,
                timeout=60,
                check=False,
            )
            (output / f"{name}.stdout").write_bytes(simulated.stdout)
            (output / f"{name}.stderr").write_bytes(simulated.stderr)
            calibrate.verify_results(simulated.stderr, cases, set(), simulated.returncode)
            observed: dict[str, CaseResult] = {}
            for kind in ("prompt", "confirm"):
                trace, lines = terminal_case(python, root / "src", kind, env)
                filename = f"{name}-{kind}.terminal"
                (output / filename).write_bytes(trace)
                expected = ["Question: z", "RESULT=z"] if kind == "prompt" else ["Question: y", "RESULT=True"]
                observed[kind] = {
                    "passed": lines == expected,
                    "lines": lines,
                    "trace": filename,
                    "sha256": digest(trace),
                }
            if calibrate.snapshot(root / "src") != variant_before:
                raise ValueError("A trusted variant changed during qualification")
            variants[name] = {
                "module_sha256": digest((root / "src/click/termui.py").read_bytes()),
                "simulated_cases": len(cases),
                "simulated_stdout_sha256": digest(simulated.stdout),
                "simulated_stderr_sha256": digest(simulated.stderr),
                "cases": observed,
            }
    if calibrate.verify_source(source) != before:
        raise ValueError("Source changed during qualification")
    if inputs != {name: digest((CONTROLS.parent / name).read_bytes()) for name in inputs}:
        raise ValueError("Control inputs changed during qualification")
    if not all(variants["entire-input-prompt"]["cases"][kind]["passed"] for kind in ("prompt", "confirm")):
        raise ValueError("The positive terminal control failed")
    if any(variants["no-workaround"]["cases"][kind]["passed"] for kind in ("prompt", "confirm")):
        raise ValueError("The no-workaround negative control was not detected")
    result = {
        "schema_version": 1,
        "scope": "Trusted POSIX PTY controls only; not an agent trial or a confined grader.",
        "source_commit": calibrate.COMMIT,
        "source_file_count": len(before),
        "source_snapshot_sha256": digest(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()),
        "runtime": runtime,
        "terminal": {"columns": 80, "rows": 24, "term": "xterm", "inputrc": "empty"},
        "control_inputs_sha256": inputs,
        "variants": variants,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
