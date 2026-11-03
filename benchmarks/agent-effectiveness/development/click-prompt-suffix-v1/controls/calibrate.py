"""Calibrate trusted Click variants; this is not a grader for agent submissions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
COMMIT = "5f86603a84e12bdec1584c15c9f982740e613c45"
TREE = "d1ed59d09082175edc5123aaeaae262dac1baa4d"
SOURCE_SHA256 = "bc062b282d9aedffcd7c42210138445587dafff89be5741b4d2086b499400510"
FIXED_SHA256 = "86a0848cd9dd53e9f35b4f2744090169581f669fc574203d2b17c85a529868c7"
PATCH_SHA256 = "ef3c8329b80795dc828f58c750dafdbaebbec8374eb2750ff141124a431e2ff9"
TREE_SHA256 = "4e1b53cf3149a002c7fb9c9e9e21a69645b38c2839f72a0cacca995ab860f24f"
LICENSE_SHA256 = "9a8ad106a394e853bfe21f42f4e72d592819a22805d991b5f3275029292b658d"

PROMPT = (b'echo(text.rstrip(" "), nl=False, err=err)', b"echo(text[:-1], nl=False, err=err)")
PROMPT_INPUT = (b'return f(" ")', b"return f(text[-1:])")
CONFIRM = (b'echo(prompt.rstrip(" "), nl=False, err=err)', b"echo(prompt[:-1], nl=False, err=err)")
CONFIRM_INPUT = (
    b'value = visible_prompt_func(" ").lower().strip()',
    b"value = visible_prompt_func(prompt[-1:]).lower().strip()",
)
REPLACEMENTS = {
    "alternative": [
        (PROMPT[0], b"echo(text.removesuffix(text[-1:]), nl=False, err=err)"),
        PROMPT_INPUT,
        (CONFIRM[0], b"echo(prompt.removesuffix(prompt[-1:]), nl=False, err=err)"),
        CONFIRM_INPUT,
    ],
    "prompt-only": [PROMPT, PROMPT_INPUT],
    "strip-trailing": [PROMPT_INPUT, CONFIRM_INPUT],
    "empty-only": [
        (PROMPT_INPUT[0], b'return f("" if not prompt_suffix else " ")'),
        (CONFIRM_INPUT[0], b'value = visible_prompt_func("" if not prompt_suffix else " ").lower().strip()'),
    ],
}
BAD_SUFFIXES = {"double_space_suffix", "empty_suffix", "punctuation_suffix", "unicode_suffix", "default_value", "retry"}
BASE_FAILURES = {f"test_{kind}_{suffix}" for kind in ("prompt", "confirm") for suffix in BAD_SUFFIXES}
EXPECTED_FAILURES = {
    "base": BASE_FAILURES,
    "upstream": set(),
    "alternative": set(),
    "prompt-only": {name for name in BASE_FAILURES if name.startswith("test_confirm_")},
    "strip-trailing": BASE_FAILURES,
    "empty-only": {
        f"test_{kind}_{suffix}"
        for kind in ("prompt", "confirm")
        for suffix in ("double_space_suffix", "punctuation_suffix", "unicode_suffix")
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def upstream_patch() -> bytes:
    """Recover exact patch bytes from the retained UTF-8 JSON transport."""
    transport = json.loads((TASK / "controls/upstream-patch.json").read_text(encoding="utf-8"))
    if (
        not isinstance(transport, dict)
        or set(transport) != {"encoding", "patch"}
        or transport["encoding"] != "utf-8"
        or not isinstance(transport["patch"], str)
    ):
        raise ValueError("Invalid upstream patch transport")
    return transport["patch"].encode("utf-8")


def snapshot(root: Path) -> dict[str, str]:
    if any(path.is_symlink() for path in root.rglob("*")):
        raise ValueError("Source tree contains a symbolic link")
    return {path.relative_to(root).as_posix(): sha256(path.read_bytes()) for path in root.rglob("*") if path.is_file()}


def verify_source(root: Path) -> dict[str, str]:
    tree_bytes = (TASK / "tree.json").read_bytes()
    if sha256(tree_bytes) != TREE_SHA256:
        raise ValueError("Source tree manifest has changed")
    manifest = json.loads(tree_bytes)["files"]
    actual = snapshot(root)
    if set(actual) != set(manifest):
        raise ValueError("Source tree is incomplete or contains extra files")
    for name, item in manifest.items():
        data = (root / name).read_bytes()
        git_blob = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        if git_blob != item["git_blob"]:
            raise ValueError(f"Source differs from the pinned Git tree: {name}")
    if actual["src/click/termui.py"] != SOURCE_SHA256:
        raise ValueError("Source module differs from its recorded SHA-256")
    return actual


def verify_results(stderr: bytes, cases: list[str], expected: set[str], returncode: int) -> list[str]:
    text = stderr.decode("utf-8").replace("\r\n", "\n")
    rows = re.findall(r"^(test_[a-z_]+) \(__main__\.Contract\.[^)]+\) \.\.\. (ok|FAIL|ERROR)$", text, re.MULTILINE)
    failed = {name for name, status in rows if status == "FAIL"}
    details = re.findall(r"^FAIL: (test_[a-z_]+) ", text, re.MULTILINE)
    summary = f"FAILED (failures={len(expected)})" if expected else "OK"
    if (
        sorted(name for name, _ in rows) != sorted(cases)
        or failed != expected
        or any(status == "ERROR" for _, status in rows)
        or sorted(details) != sorted(expected)
        or len(re.findall(rf"^Ran {len(cases)} tests in .+$", text, re.MULTILINE)) != 1
        or text.splitlines().count(summary) != 1
        or returncode != int(bool(expected))
    ):
        raise ValueError("Control observations disagree with expected case outcomes")
    return sorted(failed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True, help="Complete extracted source archive at the pinned revision"
    )
    parser.add_argument("--target-python", type=Path, default=Path(sys.executable))
    parser.add_argument("--output", type=Path, required=True, help="New directory for raw outputs and result")
    args = parser.parse_args(argv)
    source = args.source.resolve()
    output = args.output.resolve()
    if output.is_relative_to(source):
        raise ValueError("Output must be outside the source tree")
    before = verify_source(source)
    patch = upstream_patch()
    if sha256(patch) != PATCH_SHA256:
        raise ValueError("Upstream patch has changed")
    metadata = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    expected_metadata = {
        "source_commit": COMMIT,
        "source_tree": TREE,
        "source_tree_manifest_sha256": TREE_SHA256,
        "source_sha256": SOURCE_SHA256,
        "fixed_source_sha256": FIXED_SHA256,
        "upstream_patch_sha256": PATCH_SHA256,
        "upstream_patch": "controls/upstream-patch.json",
        "license_sha256": LICENSE_SHA256,
    }
    if (
        any(metadata.get(key) != value for key, value in expected_metadata.items())
        or sha256((TASK / "LICENSE").read_bytes()) != LICENSE_SHA256
    ):
        raise ValueError("Task metadata or license differs from the recorded source")
    case_manifest = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))
    cases = case_manifest["cases"]
    if case_manifest["schema_version"] != 1 or len(cases) != 16 or len(set(cases)) != 16:
        raise ValueError("Invalid case manifest")
    runtime = json.loads(
        subprocess.check_output(
            [
                str(args.target_python.absolute()),
                "-I",
                "-c",
                "import json,platform,sys; print(json.dumps({'implementation':platform.python_implementation(),'version':list(sys.version_info[:3])}))",
            ],
            timeout=30,
        )
    )
    if runtime["implementation"] != "CPython" or runtime["version"][:2] < [3, 11]:
        raise ValueError("The controls require CPython 3.11 or later")
    inputs = {
        name: sha256((TASK / name).read_bytes())
        for name in (
            "TASK.md",
            "README.md",
            "LICENSE",
            "source.json",
            "tree.json",
            "cases.json",
            "controls/calibrate.py",
            "controls/test_contract.py",
            "controls/upstream-patch.json",
        )
    }
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with tempfile.TemporaryDirectory(prefix="click-suffix-calibration-") as temporary:
        scratch = Path(temporary)
        for name, expected in EXPECTED_FAILURES.items():
            variant = scratch / name
            shutil.copytree(source / "src", variant / "src")
            module = variant / "src/click/termui.py"
            if name == "upstream":
                for check in (True, False):
                    command = ["git", "-c", "core.autocrlf=false", "apply"]
                    if check:
                        command.append("--check")
                    subprocess.run([*command, "-"], cwd=variant, input=patch, check=True, timeout=30)
                if sha256(module.read_bytes()) != FIXED_SHA256:
                    raise ValueError("Applied patch differs from the upstream fixed module")
            elif name in REPLACEMENTS:
                data = module.read_bytes()
                for old, new in REPLACEMENTS[name]:
                    if data.count(old) != 1:
                        raise ValueError(f"Replacement in {name} is missing or ambiguous")
                    data = data.replace(old, new)
                module.write_bytes(data)
            variant_before = snapshot(variant / "src")
            environment = dict(os.environ, CLICK_CONTROL_SOURCE=str(variant / "src"))
            process = subprocess.run(
                [str(args.target_python.absolute()), "-I", "-B", "-X", "utf8", "test_contract.py"],
                cwd=TASK / "controls",
                env=environment,
                capture_output=True,
                timeout=60,
                check=False,
            )
            (output / f"{name}.stdout").write_bytes(process.stdout)
            (output / f"{name}.stderr").write_bytes(process.stderr)
            failures = verify_results(process.stderr, cases, expected, process.returncode)
            if variant_before != snapshot(variant / "src"):
                raise ValueError(f"Source variant changed during {name}")
            results[name] = {
                "exit_code": process.returncode,
                "failed_cases": failures,
                "module_sha256": sha256(module.read_bytes()),
                "stdout_sha256": sha256(process.stdout),
                "stderr_sha256": sha256(process.stderr),
            }
    if before != verify_source(source) or inputs != {name: sha256((TASK / name).read_bytes()) for name in inputs}:
        raise ValueError("Source or task inputs changed during calibration")
    result = {
        "schema_version": 1,
        "status": "passed",
        "scope": "Trusted development controls, not an agent trial or a confined grader.",
        "platform": platform.platform(),
        "target_runtime": runtime,
        "source_commit": COMMIT,
        "source_file_count": len(before),
        "source_snapshot_sha256": sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()),
        "inputs_sha256": inputs,
        "case_count": len(cases),
        "variants": results,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
