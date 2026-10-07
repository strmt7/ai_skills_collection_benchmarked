#!/usr/bin/env python3
"""Track every catalog skill without treating inventory as completed research."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from _lib_b.io_utils import read_json, write_json
from build_catalog import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PHASES = ("research", "revision", "evaluation")
STATUSES = {"pending", "in_progress", "complete", "not_applicable"}


def synchronize(catalog: list[dict[str, Any]], previous: dict[str, Any]) -> dict[str, Any]:
    """Preserve work and retire disappeared entries; invalidate changed inputs."""
    if not isinstance(previous, dict):
        raise ValueError("ledger root must be an object")
    ids = [entry["id"] for entry in catalog]
    if len(ids) != len(set(ids)):
        raise ValueError("catalog has duplicate skill IDs")
    result = copy.deepcopy(previous)
    result.setdefault("ledger_version", 1)
    old = result.get("skills", {})
    retired = result.setdefault("retired_skills", {})
    if not isinstance(old, dict) or not isinstance(retired, dict):
        raise ValueError("skills and retired_skills must be ID-indexed objects")
    if not isinstance(result.get("superseded_reviews", []), list):
        raise ValueError("superseded_reviews must be a list")
    skills = {}
    for entry in sorted(catalog, key=lambda item: item["id"]):
        skill_id = entry["id"]
        state = copy.deepcopy(old.get(skill_id, retired.pop(skill_id, {})))
        if not isinstance(state, dict):
            raise ValueError(f"{skill_id}: review state must be an object")
        signature = {key: entry[key] for key in ("commit_sha", "skill_dir_sha256", "skill_file_sha256")}
        if state.get("source_signature") != signature:
            if state:
                result.setdefault("superseded_reviews", []).append({"skill_id": skill_id, "review": state})
            state = {phase: {"status": "pending", "evidence": []} for phase in PHASES}
        state.update(
            category=entry["category"],
            source_repo=entry["source_repo"],
            source_signature=signature,
            mirrored_path=entry["mirrored_path"],
        )
        skills[skill_id] = state
    retired.update({key: value for key, value in old.items() if key not in skills})
    result["skills"] = skills
    return result


def validate(ledger: dict[str, Any], root: Path) -> list[str]:
    errors = []
    if not isinstance(ledger, dict):
        return ["ledger root must be an object"]
    if ledger.get("ledger_version") != 1:
        errors.append("unsupported ledger_version")
    skills = ledger.get("skills", {})
    if not isinstance(skills, dict):
        return [*errors, "skills must be an ID-indexed object"]
    for skill_id, state in skills.items():
        if not isinstance(state, dict):
            errors.append(f"{skill_id}: review state must be an object")
            continue
        for phase in PHASES:
            record = state.get(phase, {})
            if not isinstance(record, dict):
                errors.append(f"{skill_id}/{phase}: phase record must be an object")
                continue
            status = record.get("status")
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f"{skill_id}/{phase}: invalid status")
            evidence = record.get("evidence")
            if not isinstance(evidence, list):
                errors.append(f"{skill_id}/{phase}: evidence must be a list")
                continue
            if isinstance(status, str) and status in {"complete", "not_applicable"} and not evidence:
                errors.append(f"{skill_id}/{phase}: finished status requires evidence")
            for item in evidence:
                if not isinstance(item, dict):
                    errors.append(f"{skill_id}/{phase}: evidence must contain path/hash records")
                    continue
                path = root / str(item.get("path", ""))
                if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
                    errors.append(f"{skill_id}/{phase}: missing or external evidence")
                elif hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
                    errors.append(f"{skill_id}/{phase}: evidence hash mismatch")
        research = state.get("research", {})
        if isinstance(research, dict) and "resources" in research:
            errors.extend(validate_resources(skill_id, state, root))
    gate_ids = set()
    gates = ledger.get("time_gates", [])
    if not isinstance(gates, list):
        return [*errors, "time_gates must be a list"]
    for gate in gates:
        try:
            if not isinstance(gate, dict) or not isinstance(gate.get("id"), str) or gate["id"] in gate_ids:
                errors.append("time gate IDs must be unique strings")
                continue
            gate_ids.add(gate["id"])
            parse_utc(gate["not_before_utc"])
        except (KeyError, TypeError, ValueError):
            errors.append("time gate must contain an explicit UTC not_before_utc")
    return errors


def validate_resources(skill_id: str, state: dict[str, Any], root: Path) -> list[str]:
    """Check optional resource-level progress without treating inventory as review."""
    errors = []
    hash_policy = state["research"].get("resource_hash_policy", "raw")
    if hash_policy not in ("raw", "catalog-canonical-v1"):
        return [f"{skill_id}: unsupported resource hash policy"]
    resources = state["research"]["resources"]
    if not isinstance(resources, dict):
        return [f"{skill_id}: resources must be a path-indexed object"]
    mirror = root / str(state.get("mirrored_path", ""))
    if not mirror.is_dir() or not mirror.resolve().is_relative_to(root.resolve()):
        return [f"{skill_id}: resource mirror missing or external"]
    files = {file.relative_to(mirror).as_posix(): file for file in mirror.rglob("*") if file.is_file()}
    if set(resources) != set(files):
        errors.append(f"{skill_id}: resource inventory differs from complete mirrored package")
    for name, record in resources.items():
        relative = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or ":" in name
            or relative.is_absolute()
            or relative.as_posix() != name
            or any(part in {".", ".."} for part in relative.parts)
        ):
            errors.append(f"{skill_id}: noncanonical resource path")
            continue
        if (
            not isinstance(record, dict)
            or not isinstance(record.get("status"), str)
            or record["status"] not in {"pending", "reviewed"}
        ):
            errors.append(f"{skill_id}/{name}: invalid resource status")
            continue
        file = files.get(name)
        if file is not None:
            if file.is_symlink() or not file.resolve().is_relative_to(mirror.resolve()):
                errors.append(f"{skill_id}/{name}: linked or external resource")
            elif (
                sha256_file(file)
                if hash_policy == "catalog-canonical-v1"
                else hashlib.sha256(file.read_bytes()).hexdigest()
            ) != record.get("sha256"):
                errors.append(f"{skill_id}/{name}: resource hash mismatch")
        if record["status"] == "reviewed" and (
            not isinstance(record.get("review_scope"), str) or not record["review_scope"].strip()
        ):
            errors.append(f"{skill_id}/{name}: reviewed resource requires a concrete review scope")
        if state["research"].get("status") == "complete" and record["status"] != "reviewed":
            errors.append(f"{skill_id}/{name}: completed research retains pending resources")
    return errors


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an explicit UTC string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("timestamp must be explicit UTC")
    return parsed


def gate_open(ledger: dict[str, Any], gate_id: str, at: datetime) -> bool:
    if at.tzinfo is None:
        raise ValueError("gate check requires an aware time")
    if not isinstance(ledger, dict):
        raise ValueError("ledger root must be an object")
    entries = ledger.get("time_gates", [])
    if not isinstance(entries, list) or any(not isinstance(gate, dict) for gate in entries):
        raise ValueError("time_gates must be a list of objects")
    gates = [gate for gate in entries if gate.get("id") == gate_id]
    if len(gates) != 1:
        raise ValueError(f"expected exactly one time gate named {gate_id}")
    return at >= parse_utc(gates[0]["not_before_utc"])


def summary(ledger: dict[str, Any]) -> dict[str, Any]:
    categories: dict[str, Any] = {}
    for state in ledger["skills"].values():
        counts = categories.setdefault(state["category"], {"skills": 0, **{phase: {} for phase in PHASES}})
        counts["skills"] += 1
        for phase in PHASES:
            status = state[phase]["status"]
            counts[phase][status] = counts[phase].get(status, 0) + 1
    return {"skill_count": len(ledger["skills"]), "category_count": len(categories), "categories": categories}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=ROOT / "data/improvement_ledger.json")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/skills_catalog.json")
    parser.add_argument("--check", action="store_true", help="Check coverage and evidence without changing files")
    parser.add_argument("--json", action="store_true", help="Print machine-readable coverage and errors")
    parser.add_argument("--gate", help="Check a named time gate; exit 3 while it is closed")
    parser.add_argument("--at", help="UTC time for an explicit gate check (default: current UTC)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        previous = read_json(args.ledger) if args.ledger.exists() else {"ledger_version": 1}
        if args.gate:
            at = parse_utc(args.at) if args.at else datetime.now(UTC)
            eligible = gate_open(previous, args.gate, at)
            print(json.dumps({"gate": args.gate, "eligible": eligible}, sort_keys=True))
            return 0 if eligible else 3
        updated = synchronize(read_json(args.catalog), previous)
        errors = validate(updated, ROOT)
        if args.check and updated != previous:
            errors.append("ledger coverage is stale; synchronize before recording new research")
        if not args.check and not errors:
            write_json(args.ledger, updated)
        report = {"errors": errors, "skill_count": len(updated["skills"])}
        if not errors:
            report.update(summary(updated))
        print(
            json.dumps(report, indent=2, sort_keys=True)
            if args.json
            else f"{report['skill_count']} skills; {len(errors)} errors"
        )
        return 1 if errors else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"errors": [str(exc)]}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
