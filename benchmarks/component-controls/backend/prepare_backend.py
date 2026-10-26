"""Prepare and verify source-bound API/backend component controls."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGES = ROOT / "included/improved/skills"
ARMS = ("source", "maintained")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fenced(text: str, heading: str, language: str = "typescript") -> str:
    return text.split(heading, 1)[1].split("```" + language + "\n", 1)[1].split("```", 1)[0]


def modules() -> tuple[dict[str, str], dict[str, str]]:
    api = (PACKAGES / "api-design-current/provenance/original-SKILL.md").read_text(encoding="utf-8")
    backend = (PACKAGES / "backend-patterns-current/provenance/original-SKILL.md").read_text(encoding="utf-8")
    conventions = (PACKAGES / "repository-conventions-current/provenance/original-SKILL.md").read_text(encoding="utf-8")
    post = fenced(api, "### TypeScript (Next.js API Route)")
    post = "\n".join(line for line in post.splitlines() if not line.startswith("import "))
    fragments = [post]
    for heading, end in [
        ("### Middleware Pattern", "// Usage"),
        ("### Centralized Error Handler", "// Usage"),
        ("### Retry with Exponential Backoff", "// Usage"),
        ("### Structured Logging", "const logger ="),
    ]:
        fragments.append(fenced(backend, heading).split(end, 1)[0])
    source = (HERE / "adapters/source-prefix.mts").read_text(encoding="utf-8") + "\n"
    source += "\n".join(fragments) + "\n" + (HERE / "adapters/source-suffix.mts").read_text(encoding="utf-8")
    source += "\nexport async function preserveFailure(operation: () => Promise<unknown>) {\nconst riskyOperation = operation;\n"
    source += fenced(conventions, "## Error Handling") + "\n}\n"
    go_source = (HERE / "adapters/source-go.go").read_text(encoding="utf-8")
    if "json.NewDecoder(r.Body).Decode(&req)" not in fenced(api, "### Go (net/http)", "go"):
        raise ValueError("Pinned Go excerpt changed; review rather than guessing")
    profile = (PACKAGES / "repository-conventions-current/SKILL.md").read_text(encoding="utf-8")
    profile = profile.split("```typescript\n", 1)[1].split("```", 1)[0]
    template = (HERE / "adapters/maintained.mts.template").read_text(encoding="utf-8")
    if template.count("/* PROFILE_EXCERPT */") != 1:
        raise ValueError("Exactly one profile excerpt placeholder required")
    go = (PACKAGES / "api-design-current/references/decode-json.go").read_text(encoding="utf-8")
    if not go.startswith("package httpjson\n"):
        raise ValueError("Reviewed Go package declaration changed")
    prepared = {
        "source.mts": source,
        "maintained.mts": template.replace("/* PROFILE_EXCERPT */", profile),
        "request-json.mts": (PACKAGES / "api-design-current/references/request-json.ts").read_text(encoding="utf-8"),
        "boundaries.mts": (PACKAGES / "backend-patterns-current/references/boundaries.ts").read_text(encoding="utf-8"),
        "source-go/source.go": go_source,
        "maintained-go/decode.go": go.replace("package httpjson", "package bodycontrols", 1),
        "maintained-go/fixture.go": (HERE / "adapters/maintained-go.go").read_text(encoding="utf-8"),
    }
    for arm in ARMS:
        prepared[f"{arm}-go/controls_test.go"] = (HERE / "go-controls_test.go").read_text(encoding="utf-8")
        prepared[f"{arm}-go/cases.json"] = (HERE / "go-cases.json").read_text(encoding="utf-8")
    files = [
        HERE / name
        for name in [
            "contract.json",
            "go-cases.json",
            "node-controls.mjs",
            "qualification.mjs",
            "go-controls_test.go",
            "prepare_backend.py",
            "run_backend_native.py",
            "environment.json",
            "source-provenance.json",
        ]
    ]
    files += sorted((HERE / "adapters").iterdir())
    files += [HERE.parent / "frontend" / name for name in ["package.json", "package-lock.json"]]
    files += [ROOT / "tools/_windows_owned_python.py"]
    for name in ["api-design-current", "backend-patterns-current", "repository-conventions-current"]:
        files += sorted(file for file in (PACKAGES / name).rglob("*") if file.is_file())
    bindings = {file.relative_to(ROOT).as_posix(): digest(file) for file in files}
    return prepared, bindings


def observations(native: Path) -> dict:
    contract = json.loads((HERE / "contract.json").read_text(encoding="utf-8"))
    processes = json.loads((native / "processes.json").read_text(encoding="utf-8"))
    expected_phases = {"node-version", "go-version", "go-telemetry-off", "qualification", "maintained-go-vet"}
    expected_phases |= {arm + suffix for arm in ARMS for suffix in ["-compile", "-node", "-go"]}
    if set(processes) != expected_phases:
        raise ValueError("Every declared native phase needs process evidence")
    for phase, receipt in processes.items():
        if (
            receipt.get("windows_job") is not True
            or receipt.get("kill_on_close") is not True
            or receipt.get("real_interpreter_gated_before_site") is not True
            or receipt.get("active_processes_after_cleanup") != 0
            or receipt.get("termination_reason") is not None
        ):
            raise ValueError(f"{phase}: incomplete owned process cleanup")
    arms = {}
    for arm in ARMS:
        node = json.loads((native / f"{arm}-node.stdout.log").read_text(encoding="utf-8"))
        rows = node.get("results", [])
        if (
            len(rows) != len(contract["node_contracts"])
            or {row.get("id") for row in rows} != set(contract["node_contracts"])
            or any(type(row.get("passed")) is not bool for row in rows)
        ):
            raise ValueError(f"{arm}: one boolean observation per Node contract required")
        go = {}
        for line in (native / f"{arm}-go.stdout.log").read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("Test", "").startswith("TestJSONBodyContracts/") and event["Action"] in ["pass", "fail"]:
                key = event["Test"].split("/")[-1]
                if key in go:
                    raise ValueError(f"{arm}: duplicate Go observation")
                go[key] = event["Action"] == "pass"
        if set(go) != set(contract["go_contracts"]):
            raise ValueError(f"{arm}: one observation per Go contract required")
        if processes[arm + "-node"]["exit_code"] != 0 or processes[arm + "-go"]["exit_code"] != int(
            not all(go.values())
        ):
            raise ValueError(f"{arm}: controller exits differ from observations")
        arms[arm] = {
            "node": {row["id"]: row["passed"] for row in rows},
            "go": go,
            "typecheck_exit_code": processes[arm + "-compile"]["exit_code"],
        }
    for phase in ["node-version", "go-version", "go-telemetry-off", "qualification", "maintained-go-vet"]:
        if processes[phase]["exit_code"] != 0:
            raise ValueError(f"{phase} failed")
    if json.loads((native / "qualification.stdout.log").read_text(encoding="utf-8")).get("passed") is not True:
        raise ValueError("Maintained boundary qualification failed")
    environment = json.loads((HERE / "environment.json").read_text(encoding="utf-8"))
    for phase, key in [("node-version", "node_version"), ("go-version", "go_version")]:
        if (native / f"{phase}.stdout.log").read_text(encoding="utf-8").strip() != environment[key]:
            raise ValueError(f"{phase}: runtime differs from the qualified cohort")
    return arms


def validate_result(result: dict, bindings: dict[str, str], artifact_root: Path = HERE) -> list[str]:
    errors = []
    if result.get("input_sha256") != bindings:
        errors.append("Published control inputs changed")
    if (
        result.get("measurement_kind") != "component_contract_controls"
        or result.get("agent_performance_claim") is not False
        or result.get("blind_evaluation") is not False
        or result.get("independent_model_trials") != 0
    ):
        errors.append("Component evidence cannot claim blind evaluation or agent performance")
    try:
        native = artifact_root / "native"
        actual_hashes = {path.name: digest(path) for path in native.iterdir() if path.is_file()}
        if actual_hashes != result.get("native_sha256"):
            errors.append("Native evidence missing or changed")
        actual = observations(native)
        if actual != result.get("arms"):
            errors.append("Published summary differs from native observations")
        if actual["maintained"]["typecheck_exit_code"] != 0 or not all(
            all(actual["maintained"][language].values()) for language in ["node", "go"]
        ):
            errors.append("Maintained component contract regression")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(str(error))
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="New child of the admitted Node dependency directory")
    parser.add_argument("--check", action="store_true", help="Verify exact published inputs and native observations")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    prepared, bindings = modules()
    if args.check:
        result = json.loads((HERE / "result.json").read_text(encoding="utf-8"))
        errors = validate_result(result, bindings)
        print(json.dumps({"errors": errors}))
        return int(bool(errors))
    if args.workspace is None:
        raise SystemExit("--workspace or --check is required")
    workspace = args.workspace.resolve()
    if workspace.exists():
        raise SystemExit("Workspace exists; preserve previous evidence")
    if digest(workspace.parent / "package-lock.json") != digest(HERE.parent / "frontend/package-lock.json"):
        raise SystemExit("Dependency lock differs from the qualified cohort")
    workspace.mkdir()
    for name, content in prepared.items():
        path = workspace / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    (workspace / "inputs.json").write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"arms": list(ARMS), "input_count": len(bindings)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
