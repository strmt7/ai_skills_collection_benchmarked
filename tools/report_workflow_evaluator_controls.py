#!/usr/bin/env python3
"""Recheck frozen native workflow controls without executing workflows or native tools."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/research/2026-10-08/workflow-evaluator-controls"
EXPECTED = {
    "bash-direct-template": (True, "template-injection"),
    "bash-environment-data": (False, None),
    "powershell-direct-template": (True, "template-injection"),
    "powershell-environment-data": (False, None),
    "environment-fed-eval": (True, "template-injection"),
    "checkout-mutable-ref": (True, "unpinned-uses"),
    "checkout-immutable-ref": (False, None),
}
TOOLS = ("actionlint", "zizmor")


def captured(record: dict[str, Any]) -> str:
    """Validate the exact UTF-8 capture; never interpret its contents as commands."""
    text = record["utf8"]
    raw = text.encode("utf-8")
    if (
        type(record["bytes"]) is not int
        or len(raw) != record["bytes"]
        or hashlib.sha256(raw).hexdigest() != record["sha256"]
    ):
        raise ValueError("capture byte count or SHA-256 mismatch")
    return text


def indexed(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows) or set(result) != set(EXPECTED):
        raise ValueError("controls must contain all seven distinct frozen IDs")
    return result


def basename(text: str) -> str:
    return text.replace("\\", "/").rsplit("/", 1)[-1]


def inspect(bundle: dict[str, Any]) -> dict[str, Any]:
    """Keep integrity success separate from a native evaluator's missed hazards."""
    errors: list[str] = []
    variants: list[dict[str, Any]] = []
    original: dict[str, Any] = {}
    original_digest = ""
    try:
        if (
            type(bundle["schema_version"]) is not int
            or bundle["schema_version"] != 1
            or bundle["evidence_class"] != "native-evaluator-capability-controls-not-agent-efficacy"
            or any(
                bundle[key] is not False
                for key in ("workflow_execution_performed", "new_agent_calls_performed", "agent_efficacy_scored")
            )
            or [item["revision"] for item in bundle["variants"]] != [1, 2]
            or not isinstance(bundle["limits"], list)
            or not bundle["limits"]
            or any(not isinstance(item, str) or not item.strip() for item in bundle["limits"])
        ):
            raise ValueError("invalid evidence scope or revision inventory")
        for name in TOOLS:
            tool = bundle["tools"][name]
            release = json.loads(captured(tool["release_json"]))
            version = release["tag_name"].removeprefix("v")
            expected_version_line = version if name == "actionlint" else f"zizmor {version}"
            if (
                release["draft"] is not False
                or release["prerelease"] is not False
                or captured(tool["version_output"]).partition("\n")[0].rstrip("\r") != expected_version_line
                or not captured(tool["help_output"]).strip()
            ):
                raise ValueError(f"{name}: missing native version/help capture")
            captured(tool["license"])
            qualification = tool["qualification"]
            license_name = "actionlint-LICENSE.txt" if name == "actionlint" else "zizmor-LICENSE"
            if (
                qualification["tool"] != name
                or tool["license"]["sha256"] != qualification["admitted_files"][license_name]["sha256"]
            ):
                raise ValueError(f"{name}: license qualification differs")
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        return {"ok": False, "errors": [str(exc)], "variants": [], "agent_efficacy_scored": False}

    for variant in bundle["variants"]:
        revision = variant["revision"]
        try:
            definition = json.loads(captured(variant["definition"]))
            execution = json.loads(captured(variant["execution"]))
            definitions = indexed(definition["cases"], "id")
            executions = indexed(execution["cases"], "case_id")
            cases = indexed(variant["cases"], "id")
            if (
                execution["definition_sha256"] != variant["definition"]["sha256"]
                or execution["source_inputs_unchanged"] is not True
                or execution["no_ignores_or_config_or_severity_filters"] is not True
                or execution["offline_zizmor_online_audits_not_performed"] is not True
                or execution["optional_shellcheck_and_pyflakes_not_provisioned"] is not True
                or any(
                    execution[key] is not False
                    for key in ("workflow_code_executed", "new_agent_calls", "external_llm", "agent_efficacy_scored")
                )
                or definition["expected_answers_derived_from_skill_content"] is not False
                or definition["defined_before_selected_skill_content_review"] is not (revision == 1)
            ):
                raise ValueError("definition/execution integrity or independence declarations differ")
            if revision == 1:
                original_digest = variant["definition"]["sha256"]
            elif definition["original_definition_sha256"] != original_digest:
                raise ValueError("revision 2 is not linked to the frozen original")
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            errors.append(f"revision {revision}: {exc}")
            continue

        rows = []
        for case_id, (unsafe, target_rule) in EXPECTED.items():
            try:
                case = cases[case_id]
                expected = definitions[case_id]
                run = executions[case_id]
                workflow = captured(case["workflow"])
                if (
                    expected["domain_expected_unsafe"] is not unsafe
                    or expected["candidate_native_rule"] != target_rule
                    or run["domain_expected_unsafe"] is not unsafe
                    or run["candidate_native_rule"] != target_rule
                    or expected["input_sha256"] != case["workflow"]["sha256"]
                    or run["input_sha256"] != case["workflow"]["sha256"]
                ):
                    raise ValueError("frozen ground truth or input binding differs")
                parsed = yaml.safe_load(workflow)
                if revision == 1:
                    original[case_id] = parsed
                else:
                    if (
                        expected["original_input_sha256"]
                        != indexed(bundle["variants"][0]["cases"], "id")[case_id]["workflow"]["sha256"]
                    ):
                        raise ValueError("original input digest differs")
                    if (
                        parsed["jobs"]["inspect"].pop("name") != "Inspect independent control"
                        or parsed != original[case_id]
                    ):
                        raise ValueError("revision 2 changed more than the job display name")
                findings = {}
                for name in TOOLS:
                    output = case["native_outputs"][name]
                    diagnostics = json.loads(captured(output["stdout"]))
                    captured(output["stderr"])
                    native = run[name]
                    if (
                        not isinstance(diagnostics, list)
                        or native["diagnostic_count"] != len(diagnostics)
                        or native["output_sha256"] != output["stdout"]["sha256"]
                        or native["stderr_sha256"] != output["stderr"]["sha256"]
                        or type(native["exit_code"]) is not int
                        or native["exit_code"] not in ((0, 1) if name == "actionlint" else (0, 11, 12, 13, 14))
                        or (native["exit_code"] == 0) != (not diagnostics)
                    ):
                        raise ValueError(f"{name}: native output/exit binding differs")
                    command = native["command"]
                    if basename(command[0]) != f"{name}.exe" or basename(command[-1]) != expected["input"]:
                        raise ValueError(f"{name}: native command targets another input or executable")
                    if name == "actionlint":
                        if command[1:-1] != ["-no-color", "-format", "{{json .}}"]:
                            raise ValueError("actionlint: altered control flags")
                        if any(
                            basename(item["filepath"]) != expected["input"]
                            or not 1 <= item["line"] <= len(workflow.splitlines())
                            for item in diagnostics
                        ):
                            raise ValueError("actionlint: diagnostic points outside the controlled input")
                        matched = [
                            item
                            for item in diagnostics
                            if target_rule == "template-injection"
                            and item["kind"] == "expression"
                            and '"github.event.pull_request.title" is potentially untrusted.' in item["message"]
                        ]
                        rules = [item["kind"] for item in diagnostics]
                        severities = None
                    else:
                        if (
                            command[1:-3]
                            != [
                                "--offline",
                                "--no-config",
                                "--no-ignores",
                                "--persona",
                                "auditor",
                                "--strict-collection",
                                "--no-progress",
                                "--color",
                                "never",
                                "--format",
                                "json",
                            ]
                            or command[-3] != "--cache-dir"
                        ):
                            raise ValueError("zizmor: altered offline or suppression flags")
                        if any(item["ignored"] is not False for item in diagnostics):
                            raise ValueError("zizmor: ignored diagnostic")
                        for item in diagnostics:
                            if not item["locations"] or any(
                                basename(location["symbolic"]["key"]["Local"]["verbatim_path"]) != expected["input"]
                                or not 0
                                <= location["concrete"]["location"]["start_point"]["row"]
                                < len(workflow.splitlines())
                                for location in item["locations"]
                            ):
                                raise ValueError("zizmor: diagnostic points outside the controlled input")
                        matched = [
                            item for item in diagnostics if target_rule is not None and item["ident"] == target_rule
                        ]
                        rules = [item["ident"] for item in diagnostics]
                        severities = [item["determinations"]["severity"] for item in diagnostics]
                    findings[name] = {
                        "exit_code": native["exit_code"],
                        "all_diagnostic_count": len(diagnostics),
                        "all_rules": rules,
                        "all_severities": severities,
                        "target_hazard_detected": bool(matched) if unsafe else None,
                        "no_diagnostics": not diagnostics,
                    }
                rows.append({"case_id": case_id, "domain_expected_unsafe": unsafe, "native": findings})
            except (KeyError, TypeError, ValueError, AttributeError, yaml.YAMLError) as exc:
                errors.append(f"revision {revision}/{case_id}: {exc}")
        summaries = {}
        for name in TOOLS:
            misses = [
                row["case_id"]
                for row in rows
                if row["domain_expected_unsafe"] and not row["native"][name]["target_hazard_detected"]
            ]
            safe_with_findings = [
                row["case_id"]
                for row in rows
                if not row["domain_expected_unsafe"] and not row["native"][name]["no_diagnostics"]
            ]
            summaries[name] = {
                "missed_hazards": misses,
                "domain_safe_controls_with_findings": safe_with_findings,
                "qualified_as_complete_security_grader": len(rows) == len(EXPECTED)
                and not misses
                and not safe_with_findings,
            }
        variants.append({"revision": revision, "cases": rows, "tools": summaries})
    return {
        "ok": not errors,
        "errors": errors,
        "variants": variants,
        "agent_efficacy_scored": False,
        "quality_superiority_claim_permitted": False,
        "limits": bundle["limits"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE)
    parser.add_argument("--check", action="store_true", help="Check the derived report without rewriting evidence")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = args.evidence_dir / "report.json"
    try:
        result = inspect(json.loads((args.evidence_dir / "bundle.json").read_bytes()))
        if result["ok"]:
            if args.check:
                if json.loads(output.read_bytes()) != result:
                    result["errors"].append("derived report differs from retained native evidence")
            elif not output.exists() or json.loads(output.read_bytes()) != result:
                output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    result["ok"] = not result["errors"]
    print(
        json.dumps(result, indent=2)
        if args.json
        else f"Workflow control evidence: {'valid' if result['ok'] else 'invalid'}; {len(result['errors'])} errors"
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
