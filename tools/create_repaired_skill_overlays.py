#!/usr/bin/env python3
"""Create separate repaired skill overlays for failed runtime-readiness cases.

The mirrored originals under included/skills stay immutable. Repaired overlays
are explicit derived artifacts used to test whether packaging-level defects can
be fixed without hiding the original audit findings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_skill_quality
import build_catalog
import create_independent_runtime_batch
from _lib_b import determinism as _det
from _lib_b import io_utils as _io
from _lib_b import logging_utils as _logging
from _lib_b.hashing import sha256_file as _sha256_file
from _lib_b.hashing import sha256_text as _sha256_text

RUNNER_ID = "tools/create_repaired_skill_overlays.py"
RUN_NAME = "2026-04-19-runtime-failure-repairs"
REPAIRED_ROOT = ROOT / "included" / "repaired" / "skills"
ARTIFACT_ROOT = ROOT / "artifacts" / "repaired-skill-readiness" / RUN_NAME
_LOG = logging.getLogger(RUNNER_ID)

LOCAL_LINK = re.compile(r"(?P<image>!)?\[(?P<label>[^\]]+)\]\((?P<target>[^)]+)\)")


def load_json(path: Path) -> Any:
    # Kept for backward compat with any external importers.
    return _io.read_json(path)


def write_json(path: Path, data: Any) -> None:
    _io.write_json(path, data)


# Re-exported so existing callers keep working.
sha256_text = _sha256_text
sha256_file = _sha256_file


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def yaml_scalar(value: Any) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def is_external_link(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme) or target.startswith("#") or target.startswith("mailto:")


def target_missing(skill_dir: Path, raw_target: str) -> bool:
    target = raw_target.split("#", 1)[0].strip()
    if not target or is_external_link(target):
        return False
    candidate = (skill_dir / target).resolve()
    try:
        candidate.relative_to(skill_dir.resolve())
    except ValueError:
        return True
    return not candidate.exists()


def repair_markdown_links(text: str, skill_dir: Path) -> tuple[str, list[dict[str, str]]]:
    actions: list[dict[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        target = match.group("target").strip()
        label = match.group("label").strip() or target
        if not target_missing(skill_dir, target):
            return match.group(0)
        if match.group("image"):
            replacement = f"{label} (unavailable local image target: `{target}`)"
            action_type = "replaced-missing-image-link"
        else:
            replacement = f"{label} (unavailable local link target: `{target}`)"
            action_type = "replaced-missing-markdown-link"
        actions.append({"type": action_type, "label": label, "target": target})
        return replacement

    return LOCAL_LINK.sub(replace, text), actions


def ensure_frontmatter(text: str, entry: dict[str, Any]) -> tuple[str, list[dict[str, str]]]:
    if text.startswith("---\n"):
        meta, _ = build_catalog.parse_frontmatter(text)
        if meta.get("name") and meta.get("description"):
            return text, []
    frontmatter = (
        "---\n"
        f"name: {yaml_scalar(entry['install_name'])}\n"
        f"description: {yaml_scalar(entry['description'])}\n"
        "---\n\n"
    )
    return frontmatter + text, [{"type": "added-required-frontmatter", "name": entry["install_name"]}]


def failed_runtime_artifacts() -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for artifact_path in sorted((ROOT / "artifacts" / "benchmark-runs").rglob("artifact.json")):
        artifact = load_json(artifact_path)
        if artifact.get("artifact_kind") != "independent_benchmark":
            continue
        if artifact.get("metrics", {}).get("benchmark_verdict") != "failed":
            continue
        result_path = artifact_path.parent / str(artifact.get("outputs", {}).get("path", "result.json"))
        result = load_json(result_path)
        artifacts.append(
            {
                "artifact_path": artifact_path,
                "artifact": artifact,
                "result": result,
            }
        )
    return artifacts


def clean_generated_outputs() -> None:
    if REPAIRED_ROOT.exists():
        shutil.rmtree(REPAIRED_ROOT)
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    REPAIRED_ROOT.mkdir(parents=True, exist_ok=True)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)


def copy_skill_tree(src: Path, dst: Path) -> None:
    def ignore(_: str, names: list[str]) -> set[str]:
        return {name for name in names if name in {".git", "__pycache__"}}

    shutil.copytree(src, dst, ignore=ignore)


def copy_linked_local_targets(text: str, original_dir: Path, repaired_dir: Path) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for match in LOCAL_LINK.finditer(text):
        target = match.group("target").split("#", 1)[0].split("?", 1)[0].strip()
        if not target or is_external_link(target):
            continue
        source = (original_dir / target).resolve()
        try:
            relative_source = source.relative_to(original_dir.resolve())
        except ValueError:
            continue
        if not source.exists():
            continue
        destination = repaired_dir / relative_source
        if source.is_dir():
            if destination.exists():
                continue
            copy_skill_tree(source, destination)
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        actions.append({"type": "copied-linked-local-target", "target": target})
    return actions


def repaired_path_for(entry: dict[str, Any]) -> Path:
    return REPAIRED_ROOT / "by-category" / build_catalog.slug(entry["category"]) / build_catalog.slug(entry["subcategory"]) / entry["install_name"]


def evaluate_repaired_skill(
    entry: dict[str, Any],
    original: dict[str, Any],
    repaired_dir: Path,
    scenario: dict[str, Any],
    dataset_snapshot: dict[str, Any],
    task_path: str,
    repair_record: dict[str, Any],
) -> dict[str, Any]:
    original_dir = ROOT / entry["mirrored_path"]
    original_skill = original_dir / "SKILL.md"
    repaired_skill = repaired_dir / "SKILL.md"
    repaired_text = repaired_skill.read_text(encoding="utf-8", errors="replace") if repaired_skill.is_file() else ""
    repaired_missing_links = audit_skill_quality.missing_markdown_links(repaired_dir, repaired_text) if repaired_text else []
    repaired_meta, _ = build_catalog.parse_frontmatter(repaired_text)
    checks = [
        {"name": "real_dataset_snapshot_resolved", "passed": dataset_snapshot.get("resolved") is True, "evidence": dataset_snapshot.get("repo_url") or dataset_snapshot.get("url")},
        {"name": "original_mirror_unchanged", "passed": original_skill.is_file() and build_catalog.sha256_file(original_skill) == entry["skill_file_sha256"], "evidence": entry["skill_file_sha256"]},
        {"name": "repaired_skill_file_exists", "passed": repaired_skill.is_file(), "evidence": repaired_dir.relative_to(ROOT).as_posix() + "/SKILL.md"},
        {"name": "source_text_preserved", "passed": (repaired_dir / "provenance" / "original.SKILL.md").is_file() and sha256_file(repaired_dir / "provenance" / "original.SKILL.md") == sha256_file(original_skill), "evidence": "provenance/original.SKILL.md"},
        {"name": "required_frontmatter_present_after_repair", "passed": bool(repaired_meta.get("name") and repaired_meta.get("description")), "evidence": sorted(repaired_meta.keys())},
        {"name": "local_markdown_links_resolve_after_repair", "passed": not repaired_missing_links, "evidence": repaired_missing_links},
        {"name": "same_independent_task_fixture", "passed": bool(task_path), "evidence": task_path},
        {"name": "same_non_provenance_scenario", "passed": scenario.get("dataset_track_id") != "source-skill-repository", "evidence": scenario["id"]},
        {"name": "repair_actions_recorded", "passed": bool(repair_record.get("actions")), "evidence": repair_record.get("actions", [])},
    ]
    passed = sum(1 for check in checks if check["passed"])
    total = len(checks)
    failures = [check["name"] for check in checks if not check["passed"]]
    return {
        "inputs": {
            "skill_id": entry["id"],
            "skill_name": entry["name"],
            "scenario_id": scenario["id"],
            "dataset_track_id": scenario["dataset_track_id"],
            "original_runtime_artifact": str(original["artifact_path"].relative_to(ROOT)),
            "original_mirrored_path": entry["mirrored_path"],
            "repaired_path": repaired_dir.relative_to(ROOT).as_posix(),
            "task_brief_path": task_path,
            "dataset_snapshot": dataset_snapshot,
        },
        "steps": [
            "Copied the immutable mirrored skill into a separate repaired overlay.",
            "Preserved the original SKILL.md text under provenance/original.SKILL.md.",
            "Added required frontmatter only when missing or incomplete.",
            "Replaced unresolved local Markdown links in the repaired SKILL.md with explicit unavailable-target text.",
            "Ran the same readiness checks against the repaired overlay without changing the original mirror.",
        ],
        "outputs": {
            "benchmark_verdict": "passed" if not failures else "failed",
            "score_percent": round((passed / total) * 100, 2),
            "checks": checks,
            "blocking_failures": failures,
            "repair_actions": repair_record["actions"],
        },
        "metrics": {
            "checks_passed": passed,
            "checks_total": total,
            "score_percent": round((passed / total) * 100, 2),
            "benchmark_verdict": "passed" if not failures else "failed",
            "blocking_failure_count": len(failures),
            "original_blocking_failures": original["result"]["outputs"]["blocking_failures"],
            "original_score_percent": original["result"]["metrics"]["score_percent"],
            "repaired_missing_local_link_count": len(repaired_missing_links),
            "repair_action_count": len(repair_record["actions"]),
        },
        "citations_or_paths": [
            str(original["artifact_path"].relative_to(ROOT)),
            entry["mirrored_path"] + "/SKILL.md",
            repaired_dir.relative_to(ROOT).as_posix() + "/SKILL.md",
            repaired_dir.relative_to(ROOT).as_posix() + "/provenance/original.SKILL.md",
            task_path,
            "data/benchmark_scenarios.json",
            "data/benchmark_tracks.json",
        ],
    }


def write_transcript(
    path: Path,
    entry: dict[str, Any],
    result: dict[str, Any],
    repair_record: dict[str, Any],
    dataset_snapshot: dict[str, Any],
) -> None:
    lines = [
        f"Run: {RUN_NAME}",
        f"Runner: {RUNNER_ID}",
        f"Skill: {entry['id']}",
        "",
        "Repair policy:",
        "- Original mirrored files were not edited.",
        "- The repaired overlay is separate from included/skills.",
        "- The exact original SKILL.md is preserved in the repaired overlay provenance directory.",
        "",
        "Repair actions:",
        json.dumps(repair_record["actions"], indent=2, sort_keys=True),
        "",
        "Dataset snapshot:",
        json.dumps(dataset_snapshot, indent=2, sort_keys=True),
        "",
        "Result metrics:",
        json.dumps(result["metrics"], indent=2, sort_keys=True),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_artifact(
    entry: dict[str, Any],
    scenario: dict[str, Any],
    original: dict[str, Any],
    result: dict[str, Any],
    repair_record: dict[str, Any],
    artifact_dir: Path,
    timestamp: str,
    catalog_commit: str,
) -> dict[str, Any]:
    result_path = artifact_dir / "result.json"
    transcript_path = artifact_dir / "transcript.txt"
    repair_path = artifact_dir / "repair.json"
    artifact = {
        "artifact_version": "1.0",
        "artifact_kind": "repaired_skill_readiness",
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "catalog_commit": catalog_commit,
        "source_commit": entry["commit_sha"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "runner": {
            "timestamp_utc": timestamp,
            "tool": RUNNER_ID,
            "model_or_runtime": "local-deterministic-repair-readiness-runner",
            "run_name": RUN_NAME,
        },
        "input_snapshot": {
            "kind": result["inputs"]["dataset_snapshot"]["kind"],
            "identifier": result["inputs"]["dataset_snapshot"].get("repo_url") or result["inputs"]["dataset_snapshot"].get("url"),
            "is_real": True,
            "original_runtime_artifact": str(original["artifact_path"].relative_to(ROOT)),
            "original_mirrored_path": entry["mirrored_path"],
            "repaired_path": repair_record["repaired_path"],
            "original_skill_file_sha256": entry["skill_file_sha256"],
            "repaired_skill_file_sha256": repair_record["repaired_skill_file_sha256"],
        },
        "execution": {
            "fresh_session": True,
            "commands_or_transcript_path": "transcript.txt",
        },
        "outputs": {
            "path": "result.json",
            "repair_record_path": "repair.json",
            "schema": "evaluators/repaired_skill_readiness.schema.json",
            "result_sha256": sha256_file(result_path),
            "repair_sha256": sha256_file(repair_path),
        },
        "metrics": result["metrics"],
        "independence": {
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
            "skill_content_usage": "skill text was the object under repair-readiness checks; task and expected checks were defined by the runner and original benchmark fixture",
        },
        "evidence": {
            "artifact_paths": ["result.json", "transcript.txt", "repair.json"],
            "citations_or_paths": result["citations_or_paths"],
        },
        "objective_checks": [check["name"] for check in result["outputs"]["checks"]],
    }
    write_json(artifact_dir / "artifact.json", artifact)
    return artifact


def render_manifest_doc(manifest: dict[str, Any]) -> str:
    lines = [
        "# Repaired Skill Readiness",
        "",
        "This report covers separate repaired overlays for runtime-readiness failures. It does not modify the immutable source mirrors and does not erase the original failing artifacts.",
        "",
        "## Summary",
        "",
        f"- Run: `{manifest['run_name']}`",
        f"- Repaired overlays: `{manifest['summary']['overlay_count']}`",
        f"- Repaired readiness passed: `{manifest['summary']['passed']}`",
        f"- Repaired readiness failed: `{manifest['summary']['failed']}`",
        f"- Average repaired score: `{manifest['summary']['average_score_percent']}`",
        "",
        "## Results",
        "",
        "| Skill | Original failures | Repaired verdict | Repaired score | Actions | Artifact |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in manifest["repairs"]:
        original = ", ".join(item["original_blocking_failures"]) if item["original_blocking_failures"] else "none"
        lines.append(
            f"| `{item['skill_id']}` | {original} | `{item['benchmark_verdict']}` | "
            f"{item['score_percent']} | {item['repair_action_count']} | `{item['artifact_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Use Policy",
            "",
            "Use `included/repaired/skills/` only when an explicit repaired-overlay workflow is desired. The original mirrors remain the audit baseline under `included/skills/`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _preserve_original_provenance(
    *, original_skill: Path, repaired_dir: Path, skill_id: str
) -> Path:
    """Copy the exact original SKILL.md text to the provenance dir.

    Refuses to overwrite an existing provenance copy with different bytes.
    The repair-overlay loop rule in AGENTS.md requires that the original
    SKILL.md text be preserved byte-for-byte; this helper enforces that
    invariant at the writer boundary.
    """
    provenance_dir = repaired_dir / "provenance"
    provenance_dir.mkdir(parents=True, exist_ok=True)
    dest = provenance_dir / "original.SKILL.md"
    original_hash = sha256_file(original_skill)
    if dest.is_file():
        existing_hash = sha256_file(dest)
        if existing_hash != original_hash:
            raise SystemExit(
                f"refusing to overwrite provenance for {skill_id}: "
                f"existing provenance sha256={existing_hash} differs from "
                f"current upstream sha256={original_hash}; investigate before "
                f"regenerating"
            )
    shutil.copy2(original_skill, dest)
    # Sanity check: the copy must byte-match the source.
    if sha256_file(dest) != original_hash:
        raise SystemExit(
            f"provenance copy for {skill_id} does not match upstream sha256; "
            "filesystem corruption or race detected"
        )
    return dest


def run() -> dict[str, Any]:
    existing_manifest = REPAIRED_ROOT / "manifest.json"
    existing_timestamp = _det.existing_field(existing_manifest, "generated_at_utc")
    existing_commit = _det.existing_field(existing_manifest, "catalog_commit")

    clean_generated_outputs()
    catalog = {entry["id"]: entry for entry in load_json(ROOT / "data" / "skills_catalog.json")}
    scenarios = {item["id"]: item for item in load_json(ROOT / "data" / "benchmark_scenarios.json")}
    tracks = {item["id"]: item for item in load_json(ROOT / "data" / "benchmark_tracks.json")}

    # Deterministic timestamp & commit: prefer SOURCE_DATE_EPOCH / existing
    # manifest values; fall back to the latest commit that touched the input
    # artifact set so wall-clock noise cannot leak in.
    failed_artifacts = failed_runtime_artifacts()
    fallback_epoch = _det.git_latest_commit_epoch_for(
        ROOT, [item["artifact_path"] for item in failed_artifacts]
    )
    timestamp = _det.resolve_timestamp(
        existing_manifest_value=existing_timestamp,
        fallback_epoch=fallback_epoch,
    )
    catalog_commit = _det.resolve_catalog_commit(
        root=ROOT, existing_manifest_value=existing_commit
    )
    _LOG.info(
        "repaired-overlay run: ts=%s commit=%s failed_inputs=%d",
        timestamp,
        catalog_commit,
        len(failed_artifacts),
    )
    repairs: list[dict[str, Any]] = []

    # Sort explicitly by skill_id + scenario_id for stable output ordering.
    sorted_failed = sorted(
        failed_artifacts,
        key=lambda item: (item["artifact"]["skill_id"], item["artifact"]["scenario_id"]),
    )

    for original in sorted_failed:
        skill_id = original["artifact"]["skill_id"]
        entry = catalog[skill_id]
        scenario = scenarios[original["artifact"]["scenario_id"]]
        track = tracks[scenario["dataset_track_id"]]
        original_dir = ROOT / entry["mirrored_path"]
        original_skill = original_dir / "SKILL.md"
        repaired_dir = repaired_path_for(entry)
        repaired_dir.mkdir(parents=True, exist_ok=True)
        _preserve_original_provenance(
            original_skill=original_skill,
            repaired_dir=repaired_dir,
            skill_id=skill_id,
        )

        original_text = original_skill.read_text(encoding="utf-8", errors="replace")
        text, actions = ensure_frontmatter(original_text, entry)
        text, link_actions = repair_markdown_links(text, original_dir)
        actions.extend(link_actions)
        actions.extend(copy_linked_local_targets(text, original_dir, repaired_dir))
        _io.write_text(repaired_dir / "SKILL.md", text)

        repair_record = {
            "repair_record_version": 1,
            "skill_id": skill_id,
            "original_runtime_artifact": str(original["artifact_path"].relative_to(ROOT)),
            "original_mirrored_path": entry["mirrored_path"],
            "repaired_path": repaired_dir.relative_to(ROOT).as_posix(),
            "original_skill_file_sha256": entry["skill_file_sha256"],
            "original_skill_text_sha256": sha256_text(original_text),
            "repaired_skill_file_sha256": sha256_file(repaired_dir / "SKILL.md"),
            "actions": actions,
        }
        write_json(repaired_dir / "repair.json", repair_record)

        # Always reuse the original benchmark's dataset snapshot. A fresh
        # network probe cannot produce a deterministic artifact (remote HEAD
        # moves). We record the reuse provenance in the snapshot itself.
        original_snapshot = original["result"]["inputs"].get("dataset_snapshot", {})
        if original_snapshot.get("resolved") is True:
            dataset_snapshot = dict(original_snapshot)
            dataset_snapshot["reused_from_original_artifact"] = str(
                original["artifact_path"].relative_to(ROOT)
            )
            dataset_snapshot["reuse_reason"] = (
                "deterministic regeneration: the repair-overlay loop pins to "
                "the original benchmark's recorded snapshot instead of a new "
                "live probe"
            )
        else:
            # Last resort: live probe (only reachable if the original artifact
            # itself did not resolve the snapshot).
            dataset_snapshot, _commands = (
                create_independent_runtime_batch.resolve_dataset_snapshot(track)
            )
        task_path = original["result"]["inputs"].get("task_brief_path", "")
        result = evaluate_repaired_skill(entry, original, repaired_dir, scenario, dataset_snapshot, task_path, repair_record)
        artifact_dir = ARTIFACT_ROOT / build_catalog.slug(skill_id) / build_catalog.slug(scenario["id"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        write_json(artifact_dir / "dataset_snapshot.json", dataset_snapshot)
        write_json(artifact_dir / "result.json", result)
        write_json(artifact_dir / "repair.json", repair_record)
        write_transcript(artifact_dir / "transcript.txt", entry, result, repair_record, dataset_snapshot)
        write_artifact(entry, scenario, original, result, repair_record, artifact_dir, timestamp, catalog_commit)
        repairs.append(
            {
                "skill_id": skill_id,
                "scenario_id": scenario["id"],
                "original_runtime_artifact": str(original["artifact_path"].relative_to(ROOT)),
                "repaired_path": repair_record["repaired_path"],
                "artifact_path": (artifact_dir / "artifact.json").relative_to(ROOT).as_posix(),
                "benchmark_verdict": result["metrics"]["benchmark_verdict"],
                "score_percent": result["metrics"]["score_percent"],
                "original_blocking_failures": result["metrics"]["original_blocking_failures"],
                "repair_action_count": result["metrics"]["repair_action_count"],
            }
        )

    # Sort the manifest repair list for byte-stable output regardless of
    # traversal order quirks on the input side.
    repairs.sort(key=lambda item: (item["skill_id"], item["scenario_id"]))

    passed = sum(1 for item in repairs if item["benchmark_verdict"] == "passed")
    failed = len(repairs) - passed
    average = round(sum(item["score_percent"] for item in repairs) / len(repairs), 2) if repairs else 0
    manifest = {
        "run_name": RUN_NAME,
        "artifact_kind": "repaired_skill_readiness",
        "runner": RUNNER_ID,
        "generated_at_utc": timestamp,
        "catalog_commit": catalog_commit,
        "summary": {
            "overlay_count": len(repairs),
            "passed": passed,
            "failed": failed,
            "average_score_percent": average,
        },
        "repairs": repairs,
    }
    write_json(REPAIRED_ROOT / "manifest.json", manifest)
    write_json(ARTIFACT_ROOT / "manifest.json", manifest)
    _io.write_text(ROOT / "docs" / "repaired-skill-readiness.md", render_manifest_doc(manifest))
    return manifest


def check_outputs() -> None:
    manifest_path = REPAIRED_ROOT / "manifest.json"
    artifact_manifest_path = ARTIFACT_ROOT / "manifest.json"
    doc_path = ROOT / "docs" / "repaired-skill-readiness.md"
    manifest = load_json(manifest_path)
    if load_json(artifact_manifest_path) != manifest:
        raise SystemExit("repaired skill artifact manifest differs from included manifest")
    if doc_path.read_text(encoding="utf-8") != render_manifest_doc(manifest):
        raise SystemExit("docs/repaired-skill-readiness.md is stale")
    original_count = len(failed_runtime_artifacts())
    if manifest["summary"]["overlay_count"] != original_count:
        raise SystemExit("repaired overlay count does not match failed runtime artifact count")
    catalog = {entry["id"]: entry for entry in load_json(ROOT / "data" / "skills_catalog.json")}
    for item in manifest["repairs"]:
        repaired_dir = ROOT / item["repaired_path"]
        if not (repaired_dir / "SKILL.md").is_file():
            raise SystemExit(f"missing repaired SKILL.md for {item['skill_id']}")
        provenance_copy = repaired_dir / "provenance" / "original.SKILL.md"
        if not provenance_copy.is_file():
            raise SystemExit(f"missing preserved original for {item['skill_id']}")
        # Strict provenance integrity: the preserved copy MUST match the
        # immutable upstream mirror byte-for-byte.
        entry = catalog[item["skill_id"]]
        original_skill = ROOT / entry["mirrored_path"] / "SKILL.md"
        if sha256_file(original_skill) != sha256_file(provenance_copy):
            raise SystemExit(
                f"provenance integrity failure for {item['skill_id']}: "
                "provenance/original.SKILL.md diverges from the mirrored upstream"
            )
        # The repair manifest must exist alongside the overlay.
        if not (repaired_dir / "repair.json").is_file():
            raise SystemExit(f"missing repair manifest for {item['skill_id']}")
        artifact = load_json(ROOT / item["artifact_path"])
        if artifact["metrics"]["benchmark_verdict"] != item["benchmark_verdict"]:
            raise SystemExit(f"stale repaired readiness summary for {item['skill_id']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create repaired skill overlays for failed runtime-readiness "
            "artifacts. Deterministic: rerunning with no input change "
            "produces byte-identical output (set SOURCE_DATE_EPOCH / "
            "CATALOG_COMMIT to pin, or let the tool reuse the existing "
            "manifest's values)."
        )
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Read-only: validate generated repaired overlays, provenance "
            "integrity, and rendered docs. Exits non-zero on drift."
        ),
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable DEBUG-level logging."
    )
    args = parser.parse_args()
    _logging.setup_cli_logging(RUNNER_ID, verbose=args.verbose)
    if args.check:
        check_outputs()
        print("Repaired skill overlays are current.")
        return 0
    manifest = run()
    print(
        "Repaired skill overlays: "
        f"{manifest['summary']['overlay_count']} created, "
        f"{manifest['summary']['passed']} passed, {manifest['summary']['failed']} failed."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
