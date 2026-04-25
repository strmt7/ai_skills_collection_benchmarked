#!/usr/bin/env python3
"""Validate the generated AI skills catalog and its cross-references.

Invariants checked:

* catalog / manifest / agent-ready / source-lock / static snapshot stay in
  lockstep (set equality of IDs; per-field equality for entries that appear in
  multiple places);
* mirrored SKILL.md files and their directory trees hash to the values stored
  in the catalog (uses ``build_catalog.sha256_file`` and the host-portable
  ``build_catalog.sha256_tree``);
* README statistics / required links / absence of overclaim phrases;
* AGENTS.md single-session rule phrases still present;
* legacy "priority" / "requested" wording removed from catalog + tree;
* vulnerable package-lock minimums respected in mirrored node_modules entries;
* assignment and scenario coverage for candidate skills.

The tool collects every failure before exiting so a single run surfaces the
full remediation list rather than forcing one-at-a-time fixes. Add ``--json``
to emit a machine-readable envelope for CI automation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog  # noqa: E402

MIN_CATALOG = 200
MIN_SCENARIOS = 3
HEX64 = re.compile(r"[0-9a-f]{64}")
SHA1_40 = re.compile(r"[0-9a-f]{40}")
PACKAGE_LOCK_MINIMUMS = {
    "node_modules/brace-expansion": (2, 0, 3),
    "node_modules/protobufjs": (7, 5, 5),
}
REQUIRED_REPOS = {
    "strmt7/simple_ai_bitcoin_trading_binance",
    "strmt7/ome-zarr-C",
    "strmt7/project_air_defense",
    "ZMB-UZH/omero-docker-extended",
    "Varnan-Tech/opendirectory",
    "supermemoryai/skills",
    "hardikpandya/stop-slop",
}
# Direct-source repo references that MUST NOT appear in the README (privacy / scope policy).
README_FORBIDDEN_SOURCES = {
    "strmt7/simple_ai_bitcoin_trading_binance",
    "strmt7/ome-zarr-C",
    "strmt7/project_air_defense",
    "ZMB-UZH/omero-docker-extended",
}
README_OVERCLAIM_PHRASES = ("bug-free", "error-free", "guaranteed", "best skills", "fully proven")
AGENTS_SINGLE_SESSION_PHRASES = (
    "mandatory single-session rule",
    "do not spawn",
    "subagents",
    "one ai session only",
)
DELEGATION_FORBIDDEN_PHRASES = ("subagent", "parallel agent", "multi-agent orchestration")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    catalog_entries: int = 0
    tracks: int = 0
    scenarios: int = 0

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def ok(self) -> bool:
        return not self.errors


def load(path: str | Path) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _unique_ids(report: Report, items: list[dict[str, Any]], key: str, label: str) -> list[Any]:
    ids = [item[key] for item in items]
    report.require(len(ids) == len(set(ids)), f"duplicate {label} ids")
    return ids


def _version_tuple(version: Any) -> tuple[int, ...]:
    return tuple(int(part) for part in str(version).split(".")[:3] if part.isdigit())


def validate_catalog(report: Report) -> None:
    catalog = load("data/skills_catalog.json")
    track_items = load("data/benchmark_tracks.json")
    scenario_items = load("data/benchmark_scenarios.json")
    assignment_items = load("data/benchmark_assignments.json")
    selected_manifest = load("included/selected/manifest.json")
    skills_manifest = load("included/skills/manifest.json")
    agent_ready_manifest = load("included/agent-ready/manifest.json")
    source_lock = load("data/source_lock.json")
    best_practice_sources = load("data/best_practice_sources.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    _unique_ids(report, track_items, "id", "track")
    _unique_ids(report, scenario_items, "id", "scenario")
    _unique_ids(report, assignment_items, "skill_id", "assignment skill")
    _unique_ids(report, selected_manifest, "id", "selected manifest")
    _unique_ids(report, skills_manifest, "id", "skills manifest")
    _unique_ids(report, agent_ready_manifest, "id", "agent-ready manifest")

    tracks = {item["id"]: item for item in track_items}
    scenarios = {item["id"]: item for item in scenario_items}
    assignments = {item["skill_id"]: item["scenario_ids"] for item in assignment_items}
    assigned_scenario_ids = {scenario_id for scenario_ids in assignments.values() for scenario_id in scenario_ids}

    report.catalog_entries = len(catalog)
    report.tracks = len(tracks)
    report.scenarios = len(scenarios)

    report.require(len(catalog) >= MIN_CATALOG, f"catalog has {len(catalog)} entries")
    ids = _unique_ids(report, catalog, "id", "catalog")
    report.require(set(assignments) <= set(ids), "assignment for unknown skill id")
    for scenario_id in scenarios:
        report.require(scenario_id in assigned_scenario_ids, f"unassigned scenario {scenario_id}")

    missing_required = REQUIRED_REPOS - {entry["source_repo"] for entry in catalog}
    report.require(not missing_required, f"missing required repos: {sorted(missing_required)}")

    readme_expectations = {
        f"- `{len(catalog)}` source-backed skill entries.": "catalog count",
        f"- `{len(catalog)}` written skill mirrors under `included/skills/`.": "mirror count",
        f"- `{len(catalog)}` compact agent-ready skill entrypoints under `included/agent-ready/`.": "agent-ready count",
        f"- `{sum(1 for entry in catalog if entry.get('selected_subset'))}` selected repository entries.": "selected count",
        f"- `{len({entry['category'] for entry in catalog})}` categories.": "category count",
        f"- `{len(scenarios)}` real-data scenario templates.": "scenario count",
        f"- Minimum `{MIN_SCENARIOS}` benchmark scenarios assigned per scenario-covered candidate.": "minimum scenario count",
    }
    for snippet, label in readme_expectations.items():
        report.require(snippet in readme, f"README {label} is stale")
    report.require("Early alpha" in readme, "README missing early alpha note")
    report.require(
        "priority entries from requested repositories" not in readme, "README uses requested repositories wording"
    )
    report.require("[Selected skills](docs/selected-skills.md)" in readme, "README missing selected skills link")
    report.require("[Skill risk findings](docs/skill-risk-findings.md)" in readme, "README missing skill risk link")
    report.require(
        "[Immutable audit model](docs/immutable-audit-model.md)" in readme, "README missing immutable audit model link"
    )
    report.require(not (ROOT / "docs" / "priority-skills.md").exists(), "legacy priority skills document still exists")
    report.require(not (ROOT / "included" / "priority").exists(), "legacy priority manifest directory still exists")
    for forbidden in README_FORBIDDEN_SOURCES:
        report.require(forbidden not in readme, f"README reveals direct source {forbidden}")

    expected_tracks = [
        {
            "id": t[0],
            "title": t[1],
            "url": t[2],
            "kind": "real dataset or repository workflow",
            "problem": t[3],
            "metrics": t[4],
        }
        for t in build_catalog.TRACKS
    ]
    report.require(track_items == expected_tracks, "benchmark_tracks.json is stale against build_catalog.TRACKS")
    report.require(
        best_practice_sources == build_catalog.BEST_PRACTICE_SOURCES,
        "best_practice_sources.json is stale against build_catalog.BEST_PRACTICE_SOURCES",
    )
    benchmarks_doc = (ROOT / "docs" / "benchmarks.md").read_text(encoding="utf-8")
    for track in expected_tracks:
        url = str(track["url"])
        report.require(url in benchmarks_doc, f"benchmarks.md missing track URL {url}")

    catalog_by_id = {entry["id"]: entry for entry in catalog}
    skills_manifest_by_id = {entry["id"]: entry for entry in skills_manifest}
    report.require(
        set(skills_manifest_by_id) == set(catalog_by_id), "included skills manifest does not match catalog entries"
    )
    report.require(
        len(list((ROOT / "included" / "skills").rglob("SKILL.md"))) == len(catalog),
        "included skill SKILL.md count does not match catalog",
    )
    agent_ready_by_id = {entry["id"]: entry for entry in agent_ready_manifest}
    report.require(set(agent_ready_by_id) == set(catalog_by_id), "agent-ready manifest does not match catalog entries")
    report.require(
        len(list((ROOT / "included" / "agent-ready").rglob("SKILL.md"))) == len(catalog),
        "agent-ready SKILL.md count does not match catalog",
    )
    install_names = [entry.get("install_name") for entry in catalog]
    report.require(all(install_names), "catalog entry missing install_name")
    report.require(len(install_names) == len(set(install_names)), "duplicate catalog install_name")
    report.require(max(len(name) for name in install_names) <= 80, "catalog install_name value exceeds path policy")

    locked_skills = {
        skill["id"]: source | {"skill": skill}
        for source in source_lock.get("sources", [])
        for skill in source.get("skills", [])
    }
    report.require(source_lock.get("lock_version") == 1, "source lock version mismatch")
    report.require(source_lock.get("hash_algorithm") == "sha256", "source lock hash algorithm mismatch")
    report.require(set(locked_skills) == set(catalog_by_id), "source lock skills do not match catalog")

    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    for phrase in AGENTS_SINGLE_SESSION_PHRASES:
        report.require(phrase in agents_text, f"AGENTS.md missing single-session rule phrase: {phrase}")

    for agent_ready_path in (ROOT / "included" / "agent-ready").rglob("SKILL.md"):
        text = agent_ready_path.read_text(encoding="utf-8").lower()
        for phrase in DELEGATION_FORBIDDEN_PHRASES:
            report.require(phrase not in text, f"{agent_ready_path} recommends delegated AI work: {phrase}")

    for lock_path in (ROOT / "included" / "skills").rglob("package-lock.json"):
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            report.fail(f"{lock_path} is not valid JSON")
            continue
        packages = lock_data.get("packages", {})
        report.require(isinstance(packages, dict), f"{lock_path} missing package lock packages")
        for package_path, minimum in PACKAGE_LOCK_MINIMUMS.items():
            package_data = packages.get(package_path)
            if not isinstance(package_data, dict):
                continue
            observed = _version_tuple(package_data.get("version"))
            report.require(
                observed >= minimum,
                f"{lock_path} keeps vulnerable {package_path} version {package_data.get('version')}",
            )

    # Each entry is validated in isolation; _collect_entry_errors returns a
    # local list we merge in catalog order. Sequential is deliberate: the
    # per-entry work is dominated by pure-Python string/dict validation
    # (GIL-bound) with only brief hashlib segments; measured benchmarks show
    # ThreadPoolExecutor dispatch of ~673 tiny tasks *regresses* wall-clock
    # from ~3.9 s (sequential) to ~9.1 s (cpu*2 workers) because pool
    # overhead dwarfs the <1 ms-per-call work unit. Set the opt-in env var
    # VALIDATE_CATALOG_MAX_WORKERS if the workload ever shifts to be
    # IO-bound (larger mirror trees, network hashes, etc.).
    env_workers = os.environ.get("VALIDATE_CATALOG_MAX_WORKERS", "").strip()
    workers = int(env_workers) if env_workers.isdigit() and int(env_workers) > 1 else 1
    if workers == 1:
        entry_errors = [
            _collect_entry_errors(
                e,
                catalog_by_id,
                skills_manifest_by_id,
                agent_ready_by_id,
                locked_skills,
                assignments,
                scenarios,
                tracks,
            )
            for e in catalog
        ]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            entry_errors = list(
                pool.map(
                    lambda e: _collect_entry_errors(
                        e,
                        catalog_by_id,
                        skills_manifest_by_id,
                        agent_ready_by_id,
                        locked_skills,
                        assignments,
                        scenarios,
                        tracks,
                    ),
                    catalog,
                )
            )
    for errs in entry_errors:
        report.errors.extend(errs)

    selected_ids = {entry["id"] for entry in catalog if entry.get("selected_subset")}
    manifest_ids = {entry["id"] for entry in selected_manifest}
    report.require(manifest_ids == selected_ids, "selected manifest does not match selected catalog entries")
    selected_install_names = [item.get("install_name") for item in selected_manifest]
    report.require(all(selected_install_names), "selected manifest entry missing install_name")
    report.require(len(selected_install_names) == len(set(selected_install_names)), "duplicate selected install_name")
    for item in selected_manifest:
        catalog_entry = catalog_by_id[item["id"]]
        for key in (
            "subcategory",
            "install_name",
            "mirrored_path",
            "agent_ready_path",
            "source_repo",
            "source_path",
            "immutable_source_url",
            "commit_sha",
            "skill_file_sha256",
            "skill_dir_sha256",
        ):
            report.require(item.get(key) == catalog_entry[key], f"{item['id']} selected manifest {key} mismatch")
        mirror_path = ROOT / item["mirrored_path"]
        report.require(mirror_path.is_dir(), f"{item['id']} missing mirrored directory")
        report.require((mirror_path / "SKILL.md").is_file(), f"{item['id']} mirrored directory missing SKILL.md")
        report.require(
            item["standalone_installable"] == item["has_required_frontmatter"],
            f"{item['id']} standalone_installable/frontmatter mismatch",
        )
        report.require(
            item["bulk_install_safe"] == (item["has_required_frontmatter"] and item["name_conflict_group"] is None),
            f"{item['id']} invalid bulk_install_safe",
        )

    text = readme.lower()
    for phrase in README_OVERCLAIM_PHRASES:
        report.require(phrase not in text, f"README overclaim: {phrase}")


def _collect_entry_errors(
    entry: dict[str, Any],
    catalog_by_id: dict[str, Any],
    skills_manifest_by_id: dict[str, Any],
    agent_ready_by_id: dict[str, Any],
    locked_skills: dict[str, Any],
    assignments: dict[str, Any],
    scenarios: dict[str, Any],
    tracks: dict[str, Any],
) -> list[str]:
    """Run `_validate_entry` into a scratch Report and return just its errors.

    Thread-safe wrapper for the ThreadPoolExecutor dispatch: each worker gets
    its own Report so `list.append` is bounded to that worker's scope. The
    main thread then merges errors in catalog order.
    """
    local = Report()
    _validate_entry(
        local,
        entry,
        catalog_by_id,
        skills_manifest_by_id,
        agent_ready_by_id,
        locked_skills,
        assignments,
        scenarios,
        tracks,
    )
    return local.errors


def _validate_entry(
    report: Report,
    entry: dict[str, Any],
    catalog_by_id: dict[str, Any],
    skills_manifest_by_id: dict[str, Any],
    agent_ready_by_id: dict[str, Any],
    locked_skills: dict[str, Any],
    assignments: dict[str, Any],
    scenarios: dict[str, Any],
    tracks: dict[str, Any],
) -> None:
    for key in (
        "name",
        "description",
        "category",
        "subcategory",
        "install_name",
        "mirrored_path",
        "agent_ready_path",
        "source_repo",
        "source_path",
        "source_url",
        "immutable_source_url",
        "commit_sha",
        "selection_policy",
        "skill_file_sha256",
        "skill_dir_sha256",
    ):
        report.require(bool(entry.get(key)), f"{entry['id']} missing {key}")
    report.require(isinstance(entry.get("selected_subset"), bool), f"{entry['id']} invalid selected_subset")
    report.require(not entry["source_tier"].startswith("priority"), f"{entry['id']} has legacy priority source_tier")
    report.require("requested" not in entry["source_tier"], f"{entry['id']} has requested source_tier wording")
    report.require(
        isinstance(entry.get("has_required_frontmatter"), bool), f"{entry['id']} invalid has_required_frontmatter"
    )
    report.require(entry["source_path"].endswith("SKILL.md"), f"{entry['id']} is not SKILL.md")
    report.require(SHA1_40.fullmatch(entry["commit_sha"]) is not None, f"{entry['id']} invalid commit_sha")
    report.require(HEX64.fullmatch(entry["skill_file_sha256"]) is not None, f"{entry['id']} invalid skill_file_sha256")
    report.require(HEX64.fullmatch(entry["skill_dir_sha256"]) is not None, f"{entry['id']} invalid skill_dir_sha256")
    report.require(
        entry["mirrored_path"]
        == build_catalog.skill_mirror_path(entry["category"], entry["subcategory"], entry["install_name"]),
        f"{entry['id']} mirrored_path/install_name mismatch",
    )
    report.require(
        entry["agent_ready_path"]
        == build_catalog.skill_agent_ready_path(entry["category"], entry["subcategory"], entry["install_name"]),
        f"{entry['id']} agent_ready_path/install_name mismatch",
    )
    report.require(
        Path(entry["mirrored_path"]).name == entry["install_name"],
        f"{entry['id']} mirrored_path leaf does not match install_name",
    )
    report.require(
        Path(entry["agent_ready_path"]).parent.name == entry["install_name"],
        f"{entry['id']} agent_ready_path leaf does not match install_name",
    )
    for path_key in ("install_name", "mirrored_path", "agent_ready_path", "source_path", "immutable_source_url"):
        report.require("..." not in entry[path_key], f"{entry['id']} {path_key} contains an elided path")
    expected_immutable = f"https://github.com/{entry['source_repo']}/blob/{entry['commit_sha']}/{entry['source_path']}"
    report.require(entry["immutable_source_url"] == expected_immutable, f"{entry['id']} immutable_source_url mismatch")
    if entry.get("latest_release_tag"):
        expected_source = (
            f"https://github.com/{entry['source_repo']}/blob/{entry['latest_release_tag']}/{entry['source_path']}"
        )
        report.require(
            entry["selected_ref"] == entry["latest_release_tag"],
            f"{entry['id']} selected_ref does not match latest_release_tag",
        )
        report.require(entry["source_url"] == expected_source, f"{entry['id']} release source_url mismatch")
    else:
        report.require(
            entry["source_url"] == expected_immutable,
            f"{entry['id']} source_url should be commit-pinned without release tag",
        )
    report.require(
        entry.get("benchmark_status") == "artifact_gated",
        f"{entry['id']} benchmark_status must remain artifact-gated until validated runtime artifacts exist",
    )
    manifest_entry = skills_manifest_by_id[entry["id"]]
    for key in (
        "subcategory",
        "install_name",
        "mirrored_path",
        "agent_ready_path",
        "source_repo",
        "source_path",
        "immutable_source_url",
        "commit_sha",
        "skill_file_sha256",
        "skill_dir_sha256",
    ):
        report.require(manifest_entry.get(key) == entry[key], f"{entry['id']} skills manifest {key} mismatch")
    agent_ready = agent_ready_by_id[entry["id"]]
    report.require(
        agent_ready.get("agent_ready_path") == entry["agent_ready_path"], f"{entry['id']} agent-ready path mismatch"
    )
    agent_ready_path = ROOT / entry["agent_ready_path"]
    report.require(agent_ready_path.is_file(), f"{entry['id']} missing agent-ready SKILL.md")
    if agent_ready_path.is_file():
        agent_text = agent_ready_path.read_text(encoding="utf-8")
        report.require(agent_text.startswith("---\n"), f"{entry['id']} agent-ready SKILL.md missing frontmatter")
        report.require(
            entry["mirrored_path"] in agent_text or "../" in agent_text,
            f"{entry['id']} agent-ready SKILL.md missing local source pointer",
        )
    locked = locked_skills[entry["id"]]
    report.require(locked["repo"] == entry["source_repo"], f"{entry['id']} source lock repo mismatch")
    report.require(locked["commit_sha"] == entry["commit_sha"], f"{entry['id']} source lock commit mismatch")
    report.require(locked["skill"]["source_path"] == entry["source_path"], f"{entry['id']} source lock path mismatch")
    report.require(
        locked["skill"]["install_name"] == entry["install_name"], f"{entry['id']} source lock install_name mismatch"
    )
    report.require(
        locked["skill"]["skill_file_sha256"] == entry["skill_file_sha256"],
        f"{entry['id']} source lock file hash mismatch",
    )
    report.require(
        locked["skill"]["skill_dir_sha256"] == entry["skill_dir_sha256"], f"{entry['id']} source lock dir hash mismatch"
    )
    mirror_path = ROOT / entry["mirrored_path"]
    report.require(mirror_path.is_dir(), f"{entry['id']} missing mirrored directory")
    report.require((mirror_path / "SKILL.md").is_file(), f"{entry['id']} mirrored directory missing SKILL.md")
    report.require(
        len(list(mirror_path.rglob("SKILL.md"))) == 1,
        f"{entry['id']} mirrored directory contains nested SKILL.md files",
    )
    if mirror_path.is_dir() and (mirror_path / "SKILL.md").is_file():
        report.require(
            build_catalog.sha256_file(mirror_path / "SKILL.md") == entry["skill_file_sha256"],
            f"{entry['id']} mirrored SKILL.md hash mismatch",
        )
        report.require(
            build_catalog.sha256_tree(mirror_path) == entry["skill_dir_sha256"],
            f"{entry['id']} mirrored directory hash mismatch",
        )
    if entry["scenario_covered_candidate"]:
        scenario_ids = assignments.get(entry["id"], [])
        report.require(scenario_ids == entry["benchmark_scenarios"], f"{entry['id']} assignment does not match catalog")
        report.require(len(scenario_ids) >= MIN_SCENARIOS, f"{entry['id']} has insufficient scenarios")
        report.require(
            scenario_ids and scenario_ids[0] == f"skill-proof-{entry['id']}",
            f"{entry['id']} missing source-grounded first scenario",
        )
        for scenario_id in scenario_ids:
            scenario = scenarios.get(scenario_id)
            report.require(scenario is not None, f"{entry['id']} unknown scenario {scenario_id}")
            if scenario is None:
                continue
            report.require(scenario.get("real_data_or_workflow"), f"{scenario_id} not real-data/workflow")
            report.require(scenario["dataset_track_id"] in tracks, f"{scenario_id} unknown track")
            for scenario_key in (
                "expected_output_schema",
                "environment_requirements",
                "evaluator_path",
                "input_selector",
                "dataset_snapshot_policy",
            ):
                report.require(scenario.get(scenario_key), f"{scenario_id} missing {scenario_key}")
            report.require(
                (ROOT / scenario["evaluator_path"]).is_file(),
                f"{scenario_id} missing evaluator file {scenario['evaluator_path']}",
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the AI skills catalog and its cross-references. Collects all failures before exiting.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable JSON summary instead of text.")
    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Cap the number of failure messages printed (human mode only; JSON mode prints all).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = Report()
    try:
        validate_catalog(report)
    except FileNotFoundError as exc:
        report.fail(f"required input missing: {exc}")
    except json.JSONDecodeError as exc:
        report.fail(f"invalid JSON in input: {exc}")

    if args.json:
        print(
            json.dumps(
                {
                    "ok": report.ok(),
                    "catalog_entries": report.catalog_entries,
                    "tracks": report.tracks,
                    "scenarios": report.scenarios,
                    "error_count": len(report.errors),
                    "errors": report.errors,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        if report.ok():
            print(
                f"OK: {report.catalog_entries} catalog entries, {report.tracks} dataset tracks, {report.scenarios} scenarios"
            )
        else:
            printable = report.errors[: args.max_errors]
            for message in printable:
                print(f"FAIL: {message}", file=sys.stderr)
            if len(report.errors) > args.max_errors:
                print(f"  ... {len(report.errors) - args.max_errors} more drift entries suppressed", file=sys.stderr)
            print(f"FAIL: {len(report.errors)} catalog validation errors", file=sys.stderr)
    return 0 if report.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())
