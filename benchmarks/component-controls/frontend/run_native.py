"""Rerun recorded frontend component controls in an owned Windows process tree."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import prepare

sys.path.insert(0, str(prepare.ROOT / "tools"))
from _windows_owned_python import run_python  # noqa: E402

CHILD = "import subprocess,sys; p=subprocess.run(sys.argv[1:],timeout=30); raise SystemExit(p.returncode)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--dependency-root", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="Verify the published source-bound evidence")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return prepare.main(["--check"])
    if sys.platform != "win32":
        raise SystemExit("This native qualification supports Windows only")
    if any(value is None for value in (args.node, args.dependency_root, args.workspace, args.output)):
        raise SystemExit("Explicit --node, --dependency-root, --workspace and --output are required")
    node, dependency, workspace, output = (
        value.resolve() for value in (args.node, args.dependency_root, args.workspace, args.output)
    )
    if workspace.parent != dependency or not node.is_file():
        raise SystemExit("New workspace must be directly inside the admitted dependency root; node must exist")
    expected = json.loads((prepare.HERE / "result.json").read_text(encoding="utf-8"))
    for name, version in expected["environment"]["direct_versions"].items():
        installed = json.loads((dependency / "node_modules" / name / "package.json").read_text(encoding="utf-8"))
        if installed["version"] != version:
            raise SystemExit(f"Installed dependency differs: {name}")
    output.mkdir(parents=True, exist_ok=False)
    prepare.main(["--workspace", str(workspace)])
    # Drop inherited provider credentials and Node injection options. No browser is launched.
    allowed = {"SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH", "PATHEXT"}
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    processes = {}

    def run(label: str, arguments: list[str]) -> int:
        with (
            (output / (label + ".stdout.log")).open("xb") as stdout,
            (output / (label + ".stderr.log")).open("xb") as stderr,
        ):
            code, receipt = run_python(
                sys.executable,
                CHILD,
                arguments,
                cwd=dependency,
                environment=environment,
                stdout=stdout,
                stderr=stderr,
                timeout=40,
                output_limit=1024 * 1024,
            )
        processes[label] = {**receipt, "exit_code": code}
        (output / "processes.json").write_text(json.dumps(processes, indent=2) + "\n", encoding="utf-8")
        if receipt["termination_reason"] is not None or receipt["active_processes_after_cleanup"] != 0:
            raise RuntimeError(f"Owned process control failed: {label}")
        return code

    if (
        run("node-version", [str(node), "--version"]) != 0
        or (output / "node-version.stdout.log").read_text().strip() != expected["environment"]["node_version"]
    ):
        raise SystemExit("Node runtime version differs from the recorded cohort")
    observations = {}
    errors = []
    for arm in ("locked", "upstream", "maintained"):
        code = run(
            arm + "-compile",
            [
                str(node),
                str(dependency / "node_modules/typescript/bin/tsc"),
                "--ignoreConfig",
                "--module",
                "NodeNext",
                "--target",
                "ES2022",
                "--lib",
                "ES2022,DOM",
                "--types",
                "react",
                "--strict",
                "--noEmitOnError",
                "false",
                "--outDir",
                str(workspace / "compiled"),
                str(workspace / (arm + ".mts")),
            ],
        )
        if code != expected["arms"][arm]["typecheck_exit_code"]:
            errors.append(f"{arm}: compiler exit differs from recorded evidence")
        code = run(
            arm + "-controls",
            [
                str(node),
                str(prepare.HERE / "controls.mjs"),
                str(dependency),
                str(workspace / "compiled" / (arm + ".mjs")),
            ],
        )
        if code:
            errors.append(f"{arm}: controller failed")
            continue
        observed = json.loads((output / (arm + "-controls.stdout.log")).read_text(encoding="utf-8"))
        observations[arm] = observed
        if {row["id"]: row["passed"] for row in observed["results"]} != expected["arms"][arm]["results"]:
            errors.append(f"{arm}: component contract results changed")
    code = run(
        "lifecycle",
        [str(node), str(prepare.HERE / "lifecycle.mjs"), str(dependency), str(workspace / "compiled/maintained.mjs")],
    )
    if code or json.loads((output / "lifecycle.stdout.log").read_text(encoding="utf-8")).get("passed") is not True:
        errors.append("Maintained lifecycle qualification failed")
    report = {
        "measurement_kind": "component_contract_controls",
        "agent_performance_claim": False,
        "input_sha256": json.loads((workspace / "inputs.json").read_text(encoding="utf-8")),
        "observations": observations,
        "errors": errors,
    }
    (output / "observations.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"errors": errors, "arms_recorded": sorted(observations)}))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
