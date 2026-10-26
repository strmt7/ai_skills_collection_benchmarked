"""Prepare source-bound excerpts for optional native frontend component controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fenced(text: str, heading: str) -> str:
    section = text.split(heading, 1)[1]
    return section.split("```typescript\n", 1)[1].split("```", 1)[0]


def source_module(coding: Path, frontend: Path) -> str:
    code = coding.read_text(encoding="utf-8")
    ui = frontend.read_text(encoding="utf-8")
    fetch = fenced(code, "### Error Handling").split("// FAIL:", 1)[0].strip()
    query = fenced(ui, "### Async Data Fetching Hook").split("// Usage", 1)[0].strip()
    sort = re.search(r"return (.+\.sort\([^\n]+)", fenced(ui, "### Memoization"))
    issues = re.search(r"details: (error\.[A-Za-z]+)", fenced(code, "### Input Validation"))
    if sort is None or issues is None:
        raise ValueError("Pinned excerpt anchors changed; review rather than guessing")
    return (
        "import { useState, useEffect, useCallback, useRef } from 'react';\n"
        "import { z } from 'zod';\n"
        + fetch
        + "\nexport { fetchData };\n"
        + query
        + "\nexport function sorted(markets: { volume: number }[]) {\n  return "
        + sort.group(1)
        + ";\n}\n"
        + "export function invalidIssues() {\n"
        + "  try { z.string().parse(42); } catch (error) {\n"
        + "    if (error instanceof z.ZodError) return "
        + issues.group(1)
        + ";\n    throw error;\n  }\n  return [];\n}\n"
    )


def modules() -> tuple[dict[str, str], dict[str, str]]:
    locked = ROOT / "included/improved/skills"
    sources = {
        "locked-coding": locked / "coding-standards-current/provenance/original-SKILL.md",
        "locked-frontend": locked / "frontend-patterns-current/provenance/original-SKILL.md",
        "upstream-coding": HERE / "fixtures/coding-standards-upstream.SKILL.md",
        "upstream-frontend": HERE / "fixtures/frontend-patterns-upstream.SKILL.md",
        "maintained-coding": locked / "coding-standards-current/references/contracts.ts",
        "maintained-frontend": locked / "frontend-patterns-current/references/request.ts",
    }
    prepared = {
        "locked": source_module(sources["locked-coding"], sources["locked-frontend"]),
        "upstream": source_module(sources["upstream-coding"], sources["upstream-frontend"]),
        "maintained": sources["maintained-coding"].read_text(encoding="utf-8")
        + "\n"
        + sources["maintained-frontend"].read_text(encoding="utf-8"),
    }
    bindings = {path.relative_to(ROOT).as_posix(): digest(path) for path in sources.values()}
    bindings.update(
        {
            path.relative_to(ROOT).as_posix(): digest(path)
            for path in (
                HERE / "contract.json",
                HERE / "controls.mjs",
                HERE / "lifecycle.mjs",
                HERE / "prepare.py",
                HERE / "run_native.py",
                HERE / "package.json",
                HERE / "package-lock.json",
            )
        }
    )
    return prepared, bindings


def validate_result(result: dict, bindings: dict[str, str], artifact_root: Path = HERE) -> list[str]:
    errors = []
    if result.get("input_sha256") != bindings:
        errors.append("Published control inputs changed")
    if (
        result.get("measurement_kind") != "component_contract_controls"
        or result.get("agent_performance_claim") is not False
    ):
        errors.append("Component evidence cannot claim agent performance")
    contract = json.loads((artifact_root / "contract.json").read_text(encoding="utf-8"))
    ids = set(contract["requirements"])
    arms = result.get("arms", {})
    if set(arms) != {"locked", "upstream", "maintained"}:
        errors.append("Exactly three source-bound arms required")
    for arm, record in arms.items():
        if arm not in {"locked", "upstream", "maintained"}:
            continue
        path = artifact_root / "native" / (arm + "-controls.json")
        if not path.is_file() or digest(path) != record.get("controls_sha256"):
            errors.append(f"{arm}: native controls missing or changed")
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw.get("results", [])
        if (
            len(rows) != len(ids)
            or {row.get("id") for row in rows} != ids
            or any(type(row.get("passed")) is not bool for row in rows)
        ):
            errors.append(f"{arm}: every declared contract needs one boolean result")
            continue
        observed = {row["id"]: row["passed"] for row in rows}
        if observed != record.get("results") or sum(observed.values()) != record.get("passed"):
            errors.append(f"{arm}: summary differs from native observations")
        compile_log = artifact_root / "native" / (arm + "-compile.log")
        if not compile_log.is_file() or digest(compile_log) != record.get("compile_log_sha256"):
            errors.append(f"{arm}: compiler evidence missing or changed")
        process = artifact_root / "native" / (arm + "-process.json")
        if not process.is_file() or digest(process) != record.get("process_sha256"):
            errors.append(f"{arm}: native process evidence missing or changed")
        else:
            receipts = json.loads(process.read_text(encoding="utf-8"))
            if (
                receipts["compile"]["exit_code"] != record.get("typecheck_exit_code")
                or receipts["controls"]["exit_code"] != 0
            ):
                errors.append(f"{arm}: summary differs from process exit evidence")
    lifecycle = artifact_root / "native/lifecycle.json"
    if not lifecycle.is_file() or digest(lifecycle) != result.get("lifecycle_sha256"):
        errors.append("Lifecycle qualification missing or changed")
    elif json.loads(lifecycle.read_text(encoding="utf-8")).get("passed") is not True:
        errors.append("Lifecycle qualification failed")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="New directory inside the provisioned dependency workspace")
    parser.add_argument("--check", action="store_true", help="Verify the published result's exact inputs")
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
        raise SystemExit("Workspace already exists; preserve previous evidence")
    if digest(workspace.parent / "package-lock.json") != digest(HERE / "package-lock.json"):
        raise SystemExit("Dependency lock differs from the qualified cohort")
    workspace.mkdir()
    for name, content in prepared.items():
        (workspace / (name + ".mts")).write_text(content, encoding="utf-8", newline="\n")
    (workspace / "inputs.json").write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"workspace": str(workspace), "arms": sorted(prepared)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
