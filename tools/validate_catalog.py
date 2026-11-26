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
from _lib_b import dependency_graphs  # noqa: E402
from _lib_b import source_lock as lock_format  # noqa: E402
from _source_admission import require_admitted_source  # noqa: E402
from _source_history import historical_entries  # noqa: E402

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


def _index_rows(report: Report, items: Any, key: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(items, list):
        report.fail(f"{label} must contain a list of records")
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for number, item in enumerate(items, 1):
        identity = item.get(key) if isinstance(item, dict) else None
        if not isinstance(identity, str) or not identity:
            report.fail(f"{label} row {number} requires a nonempty {key}")
        elif identity in rows:
            report.fail(f"duplicate {label} id {identity}")
        else:
            rows[identity] = item
    return rows


def _compare_membership(report: Report, observed: set[str], expected: set[str], label: str) -> None:
    for identity in sorted(expected - observed):
        report.fail(f"{label} is missing {identity}")
    for identity in sorted(observed - expected):
        report.fail(f"{label} contains unexpected {identity}")


def _required_text_fields(report: Report, row: dict[str, Any], fields: tuple[str, ...], label: str) -> bool:
    missing = [name for name in fields if not isinstance(row.get(name), str) or not row[name]]
    for name in missing:
        report.fail(f"{label} requires nonempty text in {name}")
    return not missing


MANIFEST_FIELDS = (
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
)
CATALOG_TEXT_FIELDS = (
    *MANIFEST_FIELDS,
    "name",
    "description",
    "category",
    "source_url",
    "source_tier",
    "selected_ref",
    "selection_policy",
)


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

    catalog_by_id = _index_rows(report, catalog, "id", "catalog")
    tracks = _index_rows(report, track_items, "id", "track")
    scenarios = _index_rows(report, scenario_items, "id", "scenario")
    assignment_rows = _index_rows(report, assignment_items, "skill_id", "assignment")
    selected_by_id = _index_rows(report, selected_manifest, "id", "selected manifest")
    skills_manifest_by_id = _index_rows(report, skills_manifest, "id", "skills manifest")
    agent_ready_by_id = _index_rows(report, agent_ready_manifest, "id", "agent-ready manifest")

    assignments = {}
    for identity, item in assignment_rows.items():
        assigned = item.get("scenario_ids")
        if not isinstance(assigned, list) or any(not isinstance(value, str) or not value for value in assigned):
            report.fail(f"assignment {identity} requires a list of nonempty scenario IDs")
            continue
        assignments[identity] = assigned
    assigned_scenario_ids = {scenario_id for scenario_ids in assignments.values() for scenario_id in scenario_ids}

    catalog = list(catalog_by_id.values())
    report.catalog_entries = len(catalog)
    report.tracks = len(tracks)
    report.scenarios = len(scenarios)
    report.require(len(catalog) >= MIN_CATALOG, f"catalog has {len(catalog)} entries")
    for identity in sorted(assignment_rows.keys() - catalog_by_id.keys()):
        report.fail(f"assignment for unknown skill id {identity}")
    for scenario_id in sorted(scenarios.keys() - assigned_scenario_ids):
        report.fail(f"unassigned scenario {scenario_id}")

    missing_required = REQUIRED_REPOS - {
        entry["source_repo"] for entry in catalog if isinstance(entry.get("source_repo"), str)
    }
    report.require(not missing_required, f"missing required repos: {sorted(missing_required)}")

    readme_expectations = {
        f"- `{len(catalog)}` source-backed skill entries.": "catalog count",
        f"- `{len(catalog)}` written skill mirrors under `included/skills/`.": "mirror count",
        f"- `{len(catalog)}` compact agent-ready skill entrypoints under `included/agent-ready/`.": "agent-ready count",
        f"- `{sum(1 for entry in catalog if entry.get('selected_subset'))}` selected repository entries.": "selected count",
        f"- `{len({entry['category'] for entry in catalog if isinstance(entry.get('category'), str)})}` categories.": "category count",
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

    _compare_membership(report, set(skills_manifest_by_id), set(catalog_by_id), "included skills manifest")
    report.require(
        len(list((ROOT / "included" / "skills").rglob("SKILL.md"))) == len(catalog),
        "included skill SKILL.md count does not match catalog",
    )
    _compare_membership(report, set(agent_ready_by_id), set(catalog_by_id), "agent-ready manifest")
    report.require(
        len(list((ROOT / "included" / "agent-ready").rglob("SKILL.md"))) == len(catalog),
        "agent-ready SKILL.md count does not match catalog",
    )
    install_names = [entry["install_name"] for entry in catalog if isinstance(entry.get("install_name"), str)]
    report.require(len(install_names) == len(set(install_names)), "duplicate catalog install_name")
    report.require(all(len(name) <= 80 for name in install_names), "catalog install_name value exceeds path policy")

    declared_pins = build_catalog.source_pins(build_catalog.SOURCES)
    locked_skills = {}
    locked_refs = set()
    if not isinstance(source_lock, dict):
        report.fail("source lock must contain an object")
        source_lock = {}
    for error in lock_format.metadata_errors(source_lock):
        report.fail(f"source lock: {error}")
    try:
        historical_entries(ROOT)
    except (OSError, ValueError) as exc:
        report.require(False, f"source history: {exc}")
    sources = source_lock.get("sources")
    if not isinstance(sources, list):
        sources = []
    for number, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            report.fail(f"source lock row {number} must contain an object")
            continue
        if not _required_text_fields(
            report, source, ("repo", "selected_ref", "commit_sha"), f"source lock row {number}"
        ):
            continue
        source_ref = (source["repo"], source["selected_ref"])
        report.require(source_ref not in locked_refs, f"duplicate source lock ref {source_ref}")
        locked_refs.add(source_ref)
        declared = declared_pins.get(source_ref, {})
        if "commit" in declared:
            report.require(
                source["commit_sha"] == declared["commit"],
                f"{source['repo']} source lock commit differs from the declared checkout",
            )
        upstream_repo = declared.get("upstream_repo") or source["repo"]
        if declared:
            report.require(
                source.get("local_dir") == declared["dir"],
                f"{source['repo']} source lock checkout directory differs from its declaration",
            )
        if source_lock.get("lock_version") == lock_format.LOCK_VERSION or upstream_repo != source["repo"]:
            report.require(
                source.get("origin_url") == lock_format.canonical_origin(upstream_repo),
                f"{source['repo']} canonical upstream origin differs from the declared checkout",
            )
        for skill_id, skill in _index_rows(report, source.get("skills"), "id", f"source lock {source['repo']}").items():
            if skill_id in locked_skills:
                report.fail(f"duplicate source lock skill {skill_id}")
            else:
                locked_skills[skill_id] = source | {"skill": skill, "upstream_repo": upstream_repo}
        try:
            require_admitted_source(ROOT, source["repo"], source["commit_sha"])
            build_catalog.validate_preserved_notice(ROOT, source.get("preserved_notice"), source["commit_sha"])
        except (OSError, ValueError) as error:
            report.require(False, f"{source.get('repo')}: {error}")
    _compare_membership(report, set(locked_skills), set(catalog_by_id), "source lock")

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

    selected_ids = {entry["id"] for entry in catalog if entry.get("selected_subset") is True}
    _compare_membership(report, set(selected_by_id), selected_ids, "selected manifest")
    selected_install_names = []
    for identity, item in selected_by_id.items():
        if _required_text_fields(report, item, ("install_name",), f"selected manifest {identity}"):
            selected_install_names.append(item["install_name"])
        catalog_entry = catalog_by_id.get(identity)
        if catalog_entry is not None:
            for key in MANIFEST_FIELDS:
                report.require(item.get(key) == catalog_entry.get(key), f"{identity} selected manifest {key} mismatch")
        mirror = item.get("mirrored_path")
        if isinstance(mirror, str) and mirror and catalog_entry is not None:
            mirror_path = ROOT / mirror
            report.require(mirror_path.is_dir(), f"{identity} missing mirrored directory")
            report.require((mirror_path / "SKILL.md").is_file(), f"{identity} mirrored directory missing SKILL.md")
        required = item.get("has_required_frontmatter")
        report.require(
            type(required) is bool and item.get("standalone_installable") is required,
            f"{identity} standalone_installable/frontmatter mismatch",
        )
        bulk_safe = required is True and item.get("name_conflict_group") is None
        report.require(
            "name_conflict_group" in item and item.get("bulk_install_safe") is bulk_safe,
            f"{identity} invalid bulk_install_safe",
        )
    report.require(len(selected_install_names) == len(set(selected_install_names)), "duplicate selected install_name")

    text = readme.lower()
    for phrase in README_OVERCLAIM_PHRASES:
        report.require(phrase not in text, f"README overclaim: {phrase}")


def _collect_entry_errors(
    entry: dict[str, Any],
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
        skills_manifest_by_id,
        agent_ready_by_id,
        locked_skills,
        assignments,
        scenarios,
        tracks,
    )
    return local.errors


def _validate_agent_ready_entrypoint(report: Report, entry: dict[str, Any]) -> None:
    identity = entry["id"]
    try:
        expected = build_catalog.skill_agent_ready_path(entry["category"], entry["subcategory"], entry["install_name"])
    except ValueError as error:
        report.fail(f"{identity} invalid agent-ready alias: {error}")
        return
    if entry["agent_ready_path"] != expected:
        report.fail(f"{identity} agent_ready_path differs from the canonical layout")
        return
    scenarios = entry.get("benchmark_scenarios")
    if not isinstance(scenarios, list) or any(not isinstance(value, str) or not value for value in scenarios):
        report.fail(f"{identity} cannot render agent-ready entrypoint without valid scenario IDs")
        return
    path = ROOT / expected
    try:
        actual = path.read_bytes()
    except OSError as error:
        report.fail(f"{identity} cannot read agent-ready SKILL.md: {error}")
        return
    report.require(
        actual == build_catalog.render_agent_ready_skill(entry).encode("utf-8"),
        f"{identity} generated agent-ready SKILL.md differs from the canonical layout",
    )


def _validate_entry(
    report: Report,
    entry: dict[str, Any],
    skills_manifest_by_id: dict[str, Any],
    agent_ready_by_id: dict[str, Any],
    locked_skills: dict[str, Any],
    assignments: dict[str, Any],
    scenarios: dict[str, Any],
    tracks: dict[str, Any],
) -> None:
    identity = entry["id"]
    if not _required_text_fields(report, entry, CATALOG_TEXT_FIELDS, f"catalog {identity}"):
        return
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
        Path(entry["mirrored_path"]).name == entry["install_name"],
        f"{entry['id']} mirrored_path leaf does not match install_name",
    )
    for path_key in ("install_name", "mirrored_path", "agent_ready_path", "source_path", "immutable_source_url"):
        report.require("..." not in entry[path_key], f"{entry['id']} {path_key} contains an elided path")
    locked = locked_skills.get(identity)
    if locked is not None:
        upstream = locked["upstream_repo"]
        expected_immutable = f"https://github.com/{upstream}/blob/{entry['commit_sha']}/{entry['source_path']}"
        report.require(
            entry["immutable_source_url"] == expected_immutable, f"{entry['id']} immutable_source_url mismatch"
        )
        if entry.get("latest_release_tag"):
            expected_source = f"https://github.com/{upstream}/blob/{entry['latest_release_tag']}/{entry['source_path']}"
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
    manifest_entry = skills_manifest_by_id.get(identity)
    if manifest_entry is not None:
        for key in MANIFEST_FIELDS:
            report.require(manifest_entry.get(key) == entry[key], f"{identity} skills manifest {key} mismatch")
    agent_ready = agent_ready_by_id.get(identity)
    if agent_ready is not None:
        report.require(
            agent_ready.get("agent_ready_path") == entry["agent_ready_path"], f"{identity} agent-ready path mismatch"
        )
    _validate_agent_ready_entrypoint(report, entry)
    if locked is not None:
        report.require(locked["repo"] == entry["source_repo"], f"{entry['id']} source lock repo mismatch")
        report.require(locked["commit_sha"] == entry["commit_sha"], f"{entry['id']} source lock commit mismatch")
        report.require(locked["selected_ref"] == entry["selected_ref"], f"{entry['id']} source lock ref mismatch")
        report.require(
            locked["skill"].get("source_path") == entry["source_path"], f"{entry['id']} source lock path mismatch"
        )
        report.require(
            locked["skill"].get("install_name") == entry["install_name"],
            f"{entry['id']} source lock install_name mismatch",
        )
        report.require(
            locked["skill"].get("skill_file_sha256") == entry["skill_file_sha256"],
            f"{entry['id']} source lock file hash mismatch",
        )
        report.require(
            locked["skill"].get("skill_dir_sha256") == entry["skill_dir_sha256"],
            f"{entry['id']} source lock dir hash mismatch",
        )
    policy = entry.get("credential_policy_version", 1)
    valid_policy = type(policy) is int and policy in (1, 2, 3)
    report.require(valid_policy, f"{entry['id']} unknown credential neutralization policy")
    for label, record in (
        ("source lock", locked["skill"] if locked is not None else None),
        ("manifest", manifest_entry),
    ):
        if record is None:
            continue
        report.require(
            record.get("credential_policy_version", 1) == policy,
            f"{entry['id']} {label} credential neutralization policy mismatch",
        )
        report.require(
            record.get("file_modes") == entry.get("file_modes"), f"{entry['id']} {label} file modes mismatch"
        )
        report.require(
            record.get("dependency_graph") == entry.get("dependency_graph"),
            f"{entry['id']} {label} dependency graph mismatch",
        )
    mirror_path = ROOT / entry["mirrored_path"]
    report.require(mirror_path.is_dir(), f"{entry['id']} missing mirrored directory")
    report.require((mirror_path / "SKILL.md").is_file(), f"{entry['id']} mirrored directory missing SKILL.md")
    report.require(
        len(list(mirror_path.rglob("SKILL.md"))) == 1,
        f"{entry['id']} mirrored directory contains nested SKILL.md files",
    )
    if mirror_path.is_dir() and (mirror_path / "SKILL.md").is_file():
        try:
            dependency_graphs.validate_mirror(entry, mirror_path, root=ROOT)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            report.fail(f"{entry['id']} dependency graph validation failed: {exc}")
        report.require(
            build_catalog.sha256_file(mirror_path / "SKILL.md", credential_policy=policy if valid_policy else 1)
            == entry["skill_file_sha256"],
            f"{entry['id']} mirrored SKILL.md hash mismatch",
        )
        try:
            tree_hash = build_catalog.sha256_tree(
                mirror_path, file_modes=entry.get("file_modes"), credential_policy=policy if valid_policy else 1
            )
            report.require(tree_hash == entry["skill_dir_sha256"], f"{entry['id']} mirrored directory hash mismatch")
        except (OSError, ValueError) as exc:
            report.require(False, f"{entry['id']} mirrored resource/mode validation failed: {exc}")
    covered = entry.get("scenario_covered_candidate")
    report.require(type(covered) is bool, f"{identity} invalid scenario_covered_candidate")
    if covered is True:
        scenario_ids = assignments.get(entry["id"], [])
        report.require(
            scenario_ids == entry.get("benchmark_scenarios"), f"{identity} assignment does not match catalog"
        )
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
            track = scenario.get("dataset_track_id")
            report.require(isinstance(track, str) and track in tracks, f"{scenario_id} unknown track")
            for scenario_key in (
                "expected_output_schema",
                "environment_requirements",
                "evaluator_path",
                "input_selector",
                "dataset_snapshot_policy",
            ):
                report.require(scenario.get(scenario_key), f"{scenario_id} missing {scenario_key}")
            evaluator = scenario.get("evaluator_path")
            if isinstance(evaluator, str) and evaluator:
                report.require((ROOT / evaluator).is_file(), f"{scenario_id} missing evaluator file {evaluator}")
            else:
                report.fail(f"{scenario_id} requires an evaluator path")


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
