"""Exercise native exit-status propagation in both Windows PowerShell hosts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CASES = {
    "producer_direct": r"""& $env:CONTROL_PYTHON -c 'import sys; sys.stdout.buffer.write(bytes((112,97,121,108,111,97,100))); sys.exit(7)'
exit $LASTEXITCODE
""",
    "native_pipeline": r"""& $env:CONTROL_PYTHON -c 'import sys; sys.stdout.buffer.write(bytes((112,97,121,108,111,97,100))); sys.exit(7)' | & $env:CONTROL_PYTHON -c 'import sys; sys.stdin.read(); sys.exit(0)'
Write-Output ("last=" + $LASTEXITCODE)
exit $LASTEXITCODE
""",
    "native_to_cmdlet": r"""& $env:CONTROL_PYTHON -c 'import sys; sys.exit(7)' | Out-Null
Write-Output ("last=" + $LASTEXITCODE)
exit $LASTEXITCODE
""",
    "separate_capture": r"""& $env:CONTROL_PYTHON -c 'import sys; sys.stdout.buffer.write(bytes((112,97,121,108,111,97,100))); sys.exit(7)' > $env:CONTROL_OUTPUT
$producerExit = $LASTEXITCODE
Get-Content -LiteralPath $env:CONTROL_OUTPUT | Select-Object -First 1
& $env:CONTROL_PYTHON -c 'import sys; sys.exit(0)'
exit $producerExit
""",
    "error_action_stop": r"""$ErrorActionPreference = 'Stop'
if (Get-Variable PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) { $PSNativeCommandUseErrorActionPreference = $false }
& $env:CONTROL_PYTHON -c 'import sys; sys.exit(7)'
Write-Output 'continued'
""",
    "cmdlet_stale_native_status": r"""& $env:CONTROL_PYTHON -c 'import sys; sys.exit(7)'
Get-Item -LiteralPath $env:CONTROL_MISSING -ErrorAction SilentlyContinue
$cmdletSuccess = $?
$last = $LASTEXITCODE
Write-Output ("success=$cmdletSuccess last=$last")
exit 0
""",
}

EXPECTED = {
    "producer_direct": (7, "payload"),
    "native_pipeline": (0, "last=0"),
    "native_to_cmdlet": (7, "last=7"),
    "separate_capture": (7, "payload"),
    "error_action_stop": (0, "continued"),
    "cmdlet_stale_native_status": (0, "success=False last=7"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON result file")
    parser.add_argument("--check", action="store_true", help="Verify a recorded result without running shells")
    return parser


def check_record(path: Path) -> list[str]:
    """Check recorded outcomes and bind them to this exact control source."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read recorded result: {type(exc).__name__}"]
    if not isinstance(record, dict):
        return ["recorded result must be an object"]
    errors = []
    if (
        type(record.get("schema_version")) is not int
        or record.get("schema_version") != 1
        or record.get("evidence_class") != "powershell-native-exit-status-controls"
        or record.get("passed") is not True
        or record.get("errors") != []
        or not isinstance(record.get("python_version"), str)
        or not record["python_version"]
        or not isinstance(record.get("scope"), str)
        or not record["scope"]
        or record.get("reproducer_sha256") != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    ):
        errors.append("invalid status or control-source identity")
    engines = record.get("engines")
    if not isinstance(engines, dict) or set(engines) != {"windows_powershell", "powershell"}:
        return [*errors, "both PowerShell engine results are required"]
    for name, engine in engines.items():
        if not isinstance(engine, dict) or not isinstance(engine.get("version"), str) or not engine["version"]:
            errors.append(f"{name}: version is missing")
            continue
        cases = engine.get("cases")
        if not isinstance(cases, dict) or set(cases) != set(EXPECTED):
            errors.append(f"{name}: incomplete case results")
            continue
        for case, (exit_code, stdout) in EXPECTED.items():
            observed = cases[case]
            if (
                not isinstance(observed, dict)
                or type(observed.get("returncode")) is not int
                or observed.get("returncode") != exit_code
                or observed.get("stdout") != stdout
                or observed.get("stderr") != ""
            ):
                errors.append(f"{name}/{case}: unexpected result")
    return errors


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        check_errors = check_record(args.output)
        print(json.dumps({"valid": not check_errors, "errors": check_errors}, sort_keys=True))
        return 0 if not check_errors else 1
    if args.output.exists():
        raise ValueError("choose a new output path")
    if os.name != "nt":
        raise RuntimeError("these controls require Windows PowerShell and PowerShell on Windows")
    env = os.environ.copy()
    result: dict[str, object] = {}
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="verification-powershell-") as directory:
        work = Path(directory)
        env.update(
            CONTROL_PYTHON=sys.executable,
            CONTROL_OUTPUT=str(work / "producer-output.txt"),
            CONTROL_MISSING=str(work / "not-present"),
        )
        for name, command in (("windows_powershell", "powershell.exe"), ("powershell", "pwsh.exe")):
            executable = shutil.which(command)
            if executable is None:
                errors.append(f"{command} is unavailable")
                continue
            try:
                version = (
                    subprocess.run(
                        [
                            executable,
                            "-NoLogo",
                            "-NoProfile",
                            "-NonInteractive",
                            "-Command",
                            "$PSVersionTable.PSVersion.ToString()",
                        ],
                        capture_output=True,
                        timeout=20,
                        check=True,
                    )
                    .stdout.decode("utf-8")
                    .strip()
                )
                cases: dict[str, object] = {}
                result[name] = {"version": version, "cases": cases}
                for case, script in CASES.items():
                    script_path = work / f"{name}-{case}.ps1"
                    script_path.write_text(script, encoding="utf-8", newline="\n")
                    process = subprocess.run(
                        [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(script_path)],
                        capture_output=True,
                        timeout=20,
                        env=env,
                        check=False,
                    )
                    stdout = process.stdout.decode("utf-8", errors="replace").strip()
                    stderr = process.stderr.decode("utf-8", errors="replace").strip()
                    cases[case] = {"returncode": process.returncode, "stdout": stdout, "stderr": stderr}
                    if (process.returncode, stdout) != EXPECTED[case] or stderr:
                        errors.append(f"{name}/{case}: unexpected result")
            except (OSError, UnicodeError, subprocess.SubprocessError) as exc:
                errors.append(f"{name}: {type(exc).__name__}")
    report = {
        "schema_version": 1,
        "evidence_class": "powershell-native-exit-status-controls",
        "scope": "Windows shell behavior only; not an agent trial or a skill-effectiveness score.",
        "python_version": sys.version.split()[0],
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "engines": result,
        "errors": errors,
        "passed": not errors and len(result) == 2,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
