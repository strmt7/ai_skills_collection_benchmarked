"""Calibrate additional trusted pytest controls; never grade agent submissions."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import calibrate as prior

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
CASES = {"test_direct_false_flag_preserves_debugger_order", "test_inherited_false_flag_preserves_debugger_order"}
PRESENCE_MUTANT = (
    b'            if self.config.getoption("usepdb") and not (_is_skipped(self.obj) or '
    b'hasattr(type(self._testcase), "__unittest_skip__")):'
)
VARIANTS = {"base": set(), "gold": set(), "alternative": set(), "presence-mutant": CASES}


def verify_new_observations(stderr: bytes, expected: set[str], exit_code: int) -> list[str]:
    """Reject incomplete, duplicated or inconsistent control output."""
    text = stderr.decode("utf-8").replace("\r\n", "\n")
    found = re.findall(
        r"^(test_[a-z_]+) \(test_skip_false_flag_contract\.Contract\.[^)]+\) \.\.\. (ok|FAIL|ERROR)$",
        text,
        re.MULTILINE,
    )
    names = [name for name, _ in found]
    failed = {name for name, status in found if status == "FAIL"}
    details = re.findall(r"^FAIL: (\S+)", text, re.MULTILINE)
    summary = f"FAILED (failures={len(expected)})" if expected else "OK"
    if (
        set(names) != CASES
        or len(names) != len(CASES)
        or failed != expected
        or any(status == "ERROR" for _, status in found)
        or sorted(details) != sorted(expected)
        or len(re.findall(r"^Ran 2 tests in .+$", text, re.MULTILINE)) != 1
        or text.splitlines().count(summary) != 1
        or exit_code != int(bool(expected))
    ):
        raise ValueError("False-flag observations disagree with the planned cases")
    return sorted(failed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target-python", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = args.source.resolve()
    python = args.target_python.absolute()
    output = args.output.absolute()
    if Path(os.fsdecode(prior.git(source, "rev-parse", "--show-toplevel")).strip()).resolve() != source:
        raise ValueError("Source must be the Git repository root")
    if (
        prior.git(source, "rev-parse", "HEAD").decode().strip() != prior.COMMIT
        or prior.git(source, "status", "--porcelain=v1", "--untracked-files=all").strip()
    ):
        raise ValueError("Source must be clean and at the pinned commit")
    tracked = [os.fsdecode(item) for item in prior.git(source, "ls-files", "-z").split(b"\0") if item]
    if not tracked or any(not (source / name).is_file() for name in tracked):
        raise ValueError("Pinned checkout is incomplete")
    raw = prior.git(source, "show", f"{prior.COMMIT}:src/_pytest/unittest.py")
    if (
        prior.digest(raw) != prior.SOURCE_SHA256
        or (source / "src/_pytest/unittest.py").read_bytes().replace(b"\r\n", b"\n") != raw
        or not (source / "src/_pytest/_version.py").is_file()
    ):
        raise ValueError("Source module or installed version metadata differs")
    metadata = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    if (
        metadata["source_commit"] != prior.COMMIT
        or metadata["source_sha256"] != prior.SOURCE_SHA256
        or metadata["upstream_patch_transport"] != "controls/upstream-patch.json"
        or metadata["upstream_patch_sha256"] != prior.digest(prior.upstream_patch())
        or metadata["license_sha256"] != prior.digest((TASK / "LICENSE").read_bytes())
    ):
        raise ValueError("Source provenance differs")
    probe_env = dict(os.environ, PYTHONNOUSERSITE="1")
    probe_env.pop("PYTHONPATH", None)
    probe = subprocess.check_output(
        [
            str(python),
            "-c",
            "import json,sys,importlib.metadata as m; "
            "names=['attrs','iniconfig','packaging','pluggy','py']+(['atomicwrites','colorama'] if sys.platform=='win32' else []); "
            "print(json.dumps({'python':list(sys.version_info[:3]),'venv':sys.prefix!=sys.base_prefix,"
            "'pytest':m.version('pytest'),'dependencies':{n:m.version(n) for n in names}}))",
        ],
        env=probe_env,
        timeout=30,
    )
    runtime = json.loads(probe)
    dependencies = {"attrs": "26.1.0", "iniconfig": "2.3.1", "packaging": "26.3", "pluggy": "1.7.0", "py": "1.11.0"}
    if os.name == "nt":
        dependencies.update(atomicwrites="1.4.1", colorama="0.4.6")
    if runtime != {
        "python": [3, 11, 18],
        "venv": True,
        "pytest": "7.2.0.dev173+gda9a2b584",
        "dependencies": dependencies,
    }:
        raise ValueError("Calibration requires the pinned Python 3.11.18 environment")
    old_cases = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))["cases"]
    if len(old_cases) != 25 or len(set(old_cases)) != 25:
        raise ValueError("The original case manifest differs")
    names = (
        "TASK.md",
        "LICENSE",
        "source.json",
        "cases.json",
        "controls/calibrate.py",
        "controls/test_skip_contract.py",
        "controls/calibrate_false_flag.py",
        "controls/test_skip_false_flag_contract.py",
        "controls/upstream-patch.json",
        "controls/requirements.in",
        "controls/requirements-windows.txt",
        "controls/requirements-linux.txt",
        "controls/build-requirements.in",
        "controls/build-windows.txt",
        "controls/build-linux.txt",
    )
    inputs = {name: prior.digest((TASK / name).read_bytes()) for name in names}
    before = prior.source_snapshot(source / "src")
    if not before or "_pytest/unittest.py" not in before:
        raise ValueError("The source checkout is incomplete")
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with tempfile.TemporaryDirectory(prefix="pytest-false-flag-calibration-") as directory:
        for name, expected in VARIANTS.items():
            variant = Path(directory) / name
            shutil.copytree(source / "src", variant / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
            module = variant / "src/_pytest/unittest.py"
            if name == "gold":
                subprocess.run(
                    ["git", "apply", "--check", "-"], input=prior.upstream_patch(), cwd=variant, check=True, timeout=30
                )
                subprocess.run(["git", "apply", "-"], input=prior.upstream_patch(), cwd=variant, check=True, timeout=30)
            elif name != "base":
                replacement = prior.REPLACEMENTS["alternative"] if name == "alternative" else PRESENCE_MUTANT
                data = module.read_bytes()
                if data.count(prior.ORIGINAL) != 1:
                    raise ValueError("The original condition is absent or ambiguous")
                module.write_bytes(data.replace(prior.ORIGINAL, replacement))
            variant_before = prior.source_snapshot(variant / "src")
            env = dict(
                os.environ,
                PYTEST_TARGET_SOURCE=str(variant),
                PYTEST_TARGET_PYTHON=str(python),
                PYTHONDONTWRITEBYTECODE="1",
                PYTHONUTF8="1",
                PYTHONIOENCODING="utf-8",
            )
            for suffix, test_module in (("new", "test_skip_false_flag_contract"), ("legacy", "test_skip_contract")):
                if suffix == "legacy" and name != "presence-mutant":
                    continue
                process = subprocess.run(
                    [str(python), "-m", "unittest", "-v", test_module],
                    cwd=HERE,
                    env=env,
                    capture_output=True,
                    timeout=180,
                    check=False,
                )
                (output / f"{name}-{suffix}.stdout").write_bytes(process.stdout)
                (output / f"{name}-{suffix}.stderr").write_bytes(process.stderr)
                failed = (
                    verify_new_observations(process.stderr, expected, process.returncode)
                    if suffix == "new"
                    else prior.verify_observations(process.stderr, old_cases, set(), process.returncode)
                )
                results[f"{name}-{suffix}"] = {
                    "exit_code": process.returncode,
                    "failed_cases": failed,
                    "stdout_sha256": prior.digest(process.stdout),
                    "stderr_sha256": prior.digest(process.stderr),
                }
            if variant_before != prior.source_snapshot(variant / "src"):
                raise ValueError("A trusted variant changed during calibration")
    if before != prior.source_snapshot(source / "src") or inputs != {
        name: prior.digest((TASK / name).read_bytes()) for name in names
    }:
        raise ValueError("Source or control inputs changed during calibration")
    result = {
        "schema_version": 1,
        "status": "passed",
        "scope": "Trusted development controls only; not an agent trial or confined grader.",
        "platform": platform.system(),
        "target_runtime": runtime,
        "source_commit": prior.COMMIT,
        "source_git_blob_sha256": prior.SOURCE_SHA256,
        "tracked_checkout_files": len(tracked),
        "source_snapshot_sha256": prior.digest(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()),
        "inputs_sha256": inputs,
        "new_cases": sorted(CASES),
        "legacy_case_count": len(old_cases),
        "variants": results,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
