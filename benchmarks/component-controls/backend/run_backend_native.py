"""Run API/backend component controls in an owned Windows process tree."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import prepare_backend as prepare

sys.path.insert(0, str(prepare.ROOT / "tools"))
from _windows_owned_python import run_python  # noqa: E402

CHILD = "import subprocess,sys; p=subprocess.run(sys.argv[2:],timeout=int(sys.argv[1])); raise SystemExit(p.returncode)"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path)
    parser.add_argument("--go", type=Path)
    parser.add_argument("--dependency-root", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true", help="Verify published source-bound evidence")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return prepare.main(["--check"])
    if sys.platform != "win32":
        raise SystemExit("This native qualification supports Windows only")
    if any(value is None for value in [args.node, args.go, args.dependency_root, args.workspace, args.output]):
        raise SystemExit("Explicit --node, --go, --dependency-root, --workspace and --output are required")
    node, go, dependency, workspace, output = [
        value.resolve() for value in [args.node, args.go, args.dependency_root, args.workspace, args.output]
    ]
    if workspace.parent != dependency or not node.is_file() or not go.is_file():
        raise SystemExit("Workspace must be a new dependency-root child; explicit runtime files must exist")
    environment_spec = json.loads((prepare.HERE / "environment.json").read_text(encoding="utf-8"))
    for name, version in environment_spec["direct_versions"].items():
        package = json.loads((dependency / "node_modules" / name / "package.json").read_text(encoding="utf-8"))
        if package["version"] != version:
            raise SystemExit(f"Installed dependency differs: {name}")
    output.mkdir(parents=True, exist_ok=False)
    prepare.main(["--workspace", str(workspace)])
    allowed = {"SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "PATH", "PATHEXT"}
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    state = workspace / "go-state"
    for name in ["config", "local", "gopath", "cache"]:
        (state / name).mkdir(parents=True)
    environment.update(
        APPDATA=str(state / "config"),
        LOCALAPPDATA=str(state / "local"),
        GOENV="off",
        GOTOOLCHAIN="local",
        GOWORK="off",
        GO111MODULE="off",
        GOPROXY="off",
        GOSUMDB="off",
        GOPATH=str(state / "gopath"),
        GOCACHE=str(state / "cache"),
    )
    processes = {}

    def run(label: str, arguments: list[str], cwd: Path = workspace, timeout: int = 40) -> int:
        with (
            (output / (label + ".stdout.log")).open("xb") as stdout,
            (output / (label + ".stderr.log")).open("xb") as stderr,
        ):
            code, receipt = run_python(
                sys.executable,
                CHILD,
                [str(timeout - 5), *arguments],
                cwd=cwd,
                environment=environment,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                output_limit=2 * 1024 * 1024,
            )
        processes[label] = {**receipt, "exit_code": code}
        (output / "processes.json").write_text(json.dumps(processes, indent=2) + "\n", encoding="utf-8")
        if receipt["termination_reason"] is not None or receipt["active_processes_after_cleanup"] != 0:
            raise RuntimeError(f"Owned process control failed: {label}")
        return code

    for phase, command in [
        ("node-version", [str(node), "--version"]),
        ("go-telemetry-off", [str(go), "telemetry", "off"]),
        ("go-version", [str(go), "version"]),
    ]:
        if run(phase, command):
            raise SystemExit(f"{phase} failed; evidence retained")
    for phase, key in [("node-version", "node_version"), ("go-version", "go_version")]:
        if (output / f"{phase}.stdout.log").read_text().strip() != environment_spec[key]:
            raise SystemExit(f"{phase}: runtime differs from the qualified cohort")
    for arm in prepare.ARMS:
        run(
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
                "compiled",
                arm + ".mts",
            ],
        )
        run(
            arm + "-node",
            [
                str(node),
                str(prepare.HERE / "node-controls.mjs"),
                str(dependency),
                str(workspace / "compiled" / (arm + ".mjs")),
            ],
        )
        run(arm + "-go", [str(go), "test", "-json", "-count=1"], workspace / (arm + "-go"), 150)
    run(
        "qualification",
        [str(node), str(prepare.HERE / "qualification.mjs"), str(workspace / "compiled/maintained.mjs")],
    )
    run("maintained-go-vet", [str(go), "vet", "."], workspace / "maintained-go", 150)
    observed = prepare.observations(output)
    errors = []
    recorded = prepare.HERE / "result.json"
    if recorded.is_file():
        expected = json.loads(recorded.read_text(encoding="utf-8"))
        if observed != expected["arms"]:
            errors.append("Component observations differ from published evidence")
        if json.loads((workspace / "inputs.json").read_text(encoding="utf-8")) != expected["input_sha256"]:
            errors.append("Source-bound inputs differ from published evidence")
    report = {
        "measurement_kind": "component_contract_controls",
        "agent_performance_claim": False,
        "blind_evaluation": False,
        "independent_model_trials": 0,
        "input_sha256": json.loads((workspace / "inputs.json").read_text(encoding="utf-8")),
        "arms": observed,
        "errors": errors,
    }
    (output / "observations.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "errors": errors,
                "arms": {
                    name: {language: sum(values[language].values()) for language in ["node", "go"]}
                    for name, values in observed.items()
                },
            }
        )
    )
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
