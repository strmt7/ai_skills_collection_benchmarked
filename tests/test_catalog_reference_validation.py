from __future__ import annotations

import json

import validate_catalog


def test_catalog_reports_independent_reference_drift_in_one_diagnostic_report(monkeypatch, capsys):
    load = validate_catalog.load
    catalog_file = "data/skills_catalog.json"
    ready_file = "included/agent-ready/manifest.json"
    mirror_file = "included/skills/manifest.json"
    lock_file = "data/source_lock.json"
    selected_file = "included/selected/manifest.json"
    assignment_file = "data/benchmark_assignments.json"

    catalog = load(catalog_file)
    assignments = load(assignment_file)
    assignment = assignments[0]
    first_id = assignment["skill_id"]
    first = next(item for item in catalog if item["id"] == first_id)
    first["benchmark_status"] = "owned-invalid-evidence-state"
    second_id, third_id = [item["id"] for item in catalog if item["id"] != first_id][:2]

    agent_ready = load(ready_file)
    duplicate = next(item for item in agent_ready if item["id"] != first_id)
    mirror = load(mirror_file)
    source_lock = load(lock_file)
    for source in source_lock["sources"]:
        source["skills"] = [item for item in source["skills"] if item["id"] != second_id]

    selected = load(selected_file)
    unexpected_id = "owned-unselected-record-control"
    unexpected = {**selected[0], "id": unexpected_id, "bulk_install_safe": None}

    assignment["scenario_ids"] = ["", 1]
    drifted = {
        catalog_file: catalog,
        ready_file: [item for item in agent_ready if item["id"] != first_id] + [duplicate, {"id": []}],
        mirror_file: [item for item in mirror if item["id"] != third_id],
        lock_file: source_lock,
        selected_file: [*selected, unexpected],
        assignment_file: assignments,
    }
    monkeypatch.setattr(validate_catalog, "load", lambda path: drifted[path] if path in drifted else load(path))

    assert validate_catalog.main(["--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is False
    assert report["catalog_entries"] == len(catalog)
    assert report["error_count"] == len(report["errors"])
    assert {
        f"agent-ready manifest is missing {first_id}",
        f"duplicate agent-ready manifest id {duplicate['id']}",
        f"agent-ready manifest row {len(agent_ready) + 1} requires a nonempty id",
        f"included skills manifest is missing {third_id}",
        f"source lock is missing {second_id}",
        f"selected manifest contains unexpected {unexpected_id}",
        f"{unexpected_id} invalid bulk_install_safe",
        f"assignment {first_id} requires a list of nonempty scenario IDs",
        f"{first_id} benchmark_status must remain artifact-gated until validated runtime artifacts exist",
    } <= set(report["errors"])
