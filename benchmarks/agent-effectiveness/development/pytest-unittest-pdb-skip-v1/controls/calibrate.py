"""Calibrate an exposed pytest development task; never grade an agent submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
COMMIT = "da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea"
SOURCE_SHA256 = "6a6995ff2584169db14eef86b93543179e2bbb3a2bbf8a5f6d59f6c023adcb2a"
ORIGINAL = b'            if self.config.getoption("usepdb") and not _is_skipped(self.obj):'
REPLACEMENTS = {
    "alternative": b'            if self.config.getoption("usepdb") and not (_is_skipped(self.obj) or _is_skipped(type(self._testcase))):',
    "disable-pdb-teardown": b"            if False:",
    "ignore-method-skip": b'            if self.config.getoption("usepdb") and not _is_skipped(type(self._testcase)):',
    "ignore-inherited-class-skip": b'            if self.config.getoption("usepdb") and not (_is_skipped(self.obj) or type(self._testcase).__dict__.get("__unittest_skip__", False)):',
}
EXPECTED_FAILURES = {
    "base": {
        "test_class_skip_pdb",
        "test_class_skipif_pdb",
        "test_class_skipunless_pdb",
        "test_inherited_skip_pdb",
        "test_inherited_skipif_pdb",
        "test_inherited_skipunless_pdb",
    },
    "gold": set(),
    "alternative": set(),
    "disable-pdb-teardown": {"test_failed_test_enters_debugger_before_teardown"},
    "ignore-method-skip": {"test_method_skip_pdb", "test_method_skipif_pdb", "test_method_skipunless_pdb"},
    "ignore-inherited-class-skip": {
        "test_inherited_skip_pdb",
        "test_inherited_skipif_pdb",
        "test_inherited_skipunless_pdb",
    },
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def upstream_patch() -> bytes:
    """Recover the exact public patch bytes from the retained JSON transport."""
    value = json.loads((HERE / "upstream-patch.json").read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or set(value) != {"encoding", "patch"}
        or value["encoding"] != "utf-8"
        or not isinstance(value["patch"], str)
    ):
        raise ValueError("Invalid upstream patch transport")
    return value["patch"].encode("utf-8")


def source_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): digest(path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not any(part.endswith(".egg-info") for part in path.parts)
    }


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.longpaths=true", "-C", str(source), *args], timeout=30)


def verify_observations(stderr: bytes, cases: list[str], expected: set[str], exit_code: int) -> list[str]:
    """Reject missing, duplicate or contradictory unittest observations."""
    text = stderr.decode("utf-8").replace("\r\n", "\n")
    observations = re.findall(
        r"^(test_[a-z_]+) \(test_skip_contract\.Contract\.[^)]+\) \.\.\. (ok|FAIL|ERROR)$", text, re.MULTILINE
    )
    names = [name for name, _ in observations]
    failed = {name for name, status in observations if status == "FAIL"}
    errors = [name for name, status in observations if status == "ERROR"]
    failure_details = re.findall(r"^FAIL: (\S+)", text, re.MULTILINE)
    error_details = re.findall(r"^ERROR: (\S+)", text, re.MULTILINE)
    summary = f"FAILED (failures={len(expected)})" if expected else "OK"
    if (
        sorted(names) != sorted(cases)
        or len(set(names)) != len(names)
        or failed != expected
        or errors
        or sorted(failure_details) != sorted(expected)
        or error_details
        or len(re.findall(rf"^Ran {len(cases)} tests? in .+$", text, re.MULTILINE)) != 1
        or text.splitlines().count(summary) != 1
        or exit_code != int(bool(expected))
    ):
        raise ValueError("Unittest results disagree with the planned case outcomes")
    return sorted(failed)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path, help="Clean full pytest checkout at the pinned commit")
    parser.add_argument(
        "--target-python", required=True, type=Path, help="Python 3.11 venv with the checkout installed"
    )
    parser.add_argument("--output", required=True, type=Path, help="New directory for raw controls and result")
    args = parser.parse_args(argv)
    source = args.source.resolve()
    python = args.target_python.absolute()  # Do not resolve a POSIX venv interpreter symlink.
    output = args.output.absolute()
    if Path(os.fsdecode(git(source, "rev-parse", "--show-toplevel")).strip()).resolve() != source:
        raise ValueError("Source must be the Git repository root")
    if (
        git(source, "rev-parse", "HEAD").decode().strip() != COMMIT
        or git(source, "status", "--porcelain=v1", "--untracked-files=all").strip()
    ):
        raise ValueError("Source checkout must be clean and at the pinned commit")
    tracked = [os.fsdecode(item) for item in git(source, "ls-files", "-z").split(b"\0") if item]
    if not tracked or any(not (source / name).is_file() for name in tracked):
        raise ValueError("The pinned checkout must contain all tracked files")
    raw = git(source, "show", f"{COMMIT}:src/_pytest/unittest.py")
    if digest(raw) != SOURCE_SHA256 or (source / "src/_pytest/unittest.py").read_bytes().replace(b"\r\n", b"\n") != raw:
        raise ValueError("The checked-out module differs from the pinned Git blob")
    if not (source / "src/_pytest/_version.py").is_file():
        raise ValueError("Install this checkout normally in the target venv before calibration")
    metadata = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    if (
        metadata["source_commit"] != COMMIT
        or metadata["source_sha256"] != SOURCE_SHA256
        or metadata["upstream_patch_transport"] != "controls/upstream-patch.json"
        or metadata["upstream_patch_sha256"] != digest(upstream_patch())
        or metadata["license_sha256"] != digest((TASK / "LICENSE").read_bytes())
    ):
        raise ValueError("Task provenance does not match its source and retained patch")
    probe_env = dict(os.environ, PYTHONNOUSERSITE="1")
    probe_env.pop("PYTHONPATH", None)
    probe = subprocess.check_output(
        [
            str(python),
            "-c",
            "import json,sys,importlib.metadata as m; names=['attrs','iniconfig','packaging','pluggy','py']+(['atomicwrites','colorama'] if sys.platform=='win32' else []); print(json.dumps({'python':list(sys.version_info[:3]),'venv':sys.prefix!=sys.base_prefix,'pytest':m.version('pytest'),'dependencies':{n:m.version(n) for n in names}}))",
        ],
        env=probe_env,
        timeout=30,
    )
    runtime = json.loads(probe)
    dependencies = {"attrs": "26.1.0", "iniconfig": "2.3.1", "packaging": "26.3", "pluggy": "1.7.0", "py": "1.11.0"}
    if os.name == "nt":
        dependencies.update(atomicwrites="1.4.1", colorama="0.4.6")
    if (
        runtime["venv"] is not True
        or runtime["python"][:2] != [3, 11]
        or runtime["pytest"] != "7.2.0.dev173+gda9a2b584"
        or runtime["dependencies"] != dependencies
    ):
        raise ValueError("Calibration requires the recorded Python 3.11 runtime and dependency versions")
    manifest = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))
    cases = manifest["cases"]
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != 1
        or not isinstance(cases, list)
        or any(not isinstance(name, str) or not name for name in cases)
        or len(cases) != 25
        or len(set(cases)) != len(cases)
    ):
        raise ValueError("The declared case list is invalid")
    inputs = {
        name: digest((TASK / name).read_bytes())
        for name in (
            "TASK.md",
            "LICENSE",
            "source.json",
            "cases.json",
            "controls/calibrate.py",
            "controls/test_skip_contract.py",
            "controls/upstream-patch.json",
            "controls/requirements.in",
            "controls/requirements-windows.txt",
            "controls/requirements-linux.txt",
            "controls/build-requirements.in",
            "controls/build-windows.txt",
            "controls/build-linux.txt",
        )
    }
    before = source_snapshot(source / "src")
    if not before or "_pytest/unittest.py" not in before:
        raise ValueError("The source checkout is incomplete")
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with tempfile.TemporaryDirectory(prefix="pytest-skip-calibration-") as temporary:
        scratch = Path(temporary)
        for name, expected in EXPECTED_FAILURES.items():
            variant = scratch / name
            shutil.copytree(source / "src", variant / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
            module = variant / "src/_pytest/unittest.py"
            if name == "gold":
                subprocess.run(
                    ["git", "apply", "--check", "-"], input=upstream_patch(), cwd=variant, check=True, timeout=30
                )
                subprocess.run(["git", "apply", "-"], input=upstream_patch(), cwd=variant, check=True, timeout=30)
            elif name in REPLACEMENTS:
                data = module.read_bytes()
                if data.count(ORIGINAL) != 1:
                    raise ValueError("The original condition is absent or ambiguous")
                module.write_bytes(data.replace(ORIGINAL, REPLACEMENTS[name]))
            variant_before = source_snapshot(variant / "src")
            environment = dict(
                os.environ,
                PYTEST_TARGET_SOURCE=str(variant),
                PYTEST_TARGET_PYTHON=str(python),
                PYTHONDONTWRITEBYTECODE="1",
            )
            process = subprocess.run(
                [str(python), "-m", "unittest", "-v", "test_skip_contract"],
                cwd=HERE,
                env=environment,
                capture_output=True,
                timeout=180,
                check=False,
            )
            (output / f"{name}.stdout").write_bytes(process.stdout)
            (output / f"{name}.stderr").write_bytes(process.stderr)
            try:
                failures = verify_observations(process.stderr, cases, expected, process.returncode)
            except ValueError as exc:
                raise ValueError(f"Unexpected calibration outcome for {name}; see retained raw output") from exc
            if variant_before != source_snapshot(variant / "src"):
                raise ValueError(f"Unexpected calibration outcome for {name}; see retained raw output")
            results[name] = {
                "exit_code": process.returncode,
                "failed_cases": failures,
                "module_sha256": digest(module.read_bytes()),
                "stdout_sha256": digest(process.stdout),
                "stderr_sha256": digest(process.stderr),
            }
    if before != source_snapshot(source / "src") or inputs != {
        name: digest((TASK / name).read_bytes()) for name in inputs
    }:
        raise ValueError("Source or calibration inputs changed during execution")
    result = {
        "schema_version": 1,
        "status": "passed",
        "scope": "Development controls for trusted variants; not an agent trial or a confined grader.",
        "platform": platform.system(),
        "target_runtime": runtime,
        "source_commit": COMMIT,
        "source_git_blob_sha256": SOURCE_SHA256,
        "source_file_count": len(before),
        "tracked_checkout_files": len(tracked),
        "source_snapshot_sha256": digest(json.dumps(before, sort_keys=True, separators=(",", ":")).encode("utf-8")),
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
