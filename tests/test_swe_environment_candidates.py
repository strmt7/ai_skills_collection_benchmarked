"""Keep environment candidates bound to the cohort without admitting execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks/agent-effectiveness/development/swe-skills-pilot-v1"
EVIDENCE = ROOT / "artifacts/research/2026-11-13/swe-toolchain-capsule"


def test_candidates_retain_every_fixed_task_and_every_condition() -> None:
    raw = (PILOT / "selection.json").read_bytes()
    selection = json.loads(raw)
    proposal = json.loads((PILOT / "environment-candidates.json").read_bytes())
    metadata = json.loads((EVIDENCE / "selected-environment-metadata.json").read_bytes())
    digest = hashlib.sha256(raw).hexdigest()
    assert proposal["selection_sha256"] == metadata["selection_sha256"] == digest
    expected = {row["task_id"] for row in selection["selected"]}
    assigned = [name for profile in proposal["profiles"] for name in profile["task_ids"]]
    assert set(assigned) == expected and len(assigned) == len(expected) == proposal["planned_tasks"]
    assert proposal["conditions"] == selection["conditions"]
    assert proposal["planned_attempts"] == selection["planned_attempts"] == len(assigned) * len(proposal["conditions"])
    source = {row["task_id"]: row for row in metadata["rows"]}
    assert len(proposal["profiles"]) == len({row["base_image"] for row in source.values()})
    for profile in proposal["profiles"]:
        assert all(source[name]["base_image"] == profile["author_image"] for name in profile["task_ids"])
        for key in (
            "source_equivalence_established",
            "selected_task_dependencies_qualified",
            "subject_tool_access_qualified",
            "original_scorer_qualified_for_selected_tasks",
            "execution_admitted",
        ):
            assert profile[key] is False
    for key in ("runtime_admitted", "execution_admitted", "complete_preregistration", "agent_efficacy_established"):
        assert proposal[key] is False
    assert proposal["model_invocations"] == 0
    assert metadata["task_briefs_or_evaluator_implementations_read"] is False


def test_candidates_distinguish_source_manifests_from_source_derived_proposals() -> None:
    proposal = json.loads((PILOT / "environment-candidates.json").read_bytes())
    registry = json.loads((EVIDENCE / "registry-inventory.json").read_bytes())
    original = {row["author_image"]: row for row in registry}
    previous = json.loads(
        (ROOT / "artifacts/research/2026-11-13/swe-environment-feasibility/registry-protocol.json").read_bytes()
    )
    protocol = {row["repository"]: row for row in previous["cases"]}
    captured = unavailable = 0
    for profile in proposal["profiles"]:
        origin = original[profile["author_image"]]
        assert origin["image_payload_admitted"] is False
        if origin["status"] == "manifest-captured":
            captured += 1
            assert profile["route"] == "original-image-digest-candidate"
            assert profile["candidate_image_reference"] == origin["immutable_reference"]
            assert origin["platform"] == {"architecture": "amd64", "os": "linux"}
        else:
            unavailable += 1
            assert origin["immutable_reference"] is None
            assert origin["manifest_status"] == protocol[origin["author_image"]]["manifest_status"] == 401
            assert origin["manifest_body_sha256"] == protocol[origin["author_image"]]["manifest_body_sha256"]
            assert profile["route"].startswith("source-derived-")
            assert "@sha256:" in profile["candidate_image_reference"]
    assert captured == 5 and unavailable == 2
    assert proposal["source_network_mode"] == "bridge" and proposal["qualified_component_network"] == "none"
    assert proposal["source_container_backend"] == "enroot"
    assert (
        proposal["subject_platform_current_controller"] == "Windows" and proposal["capsule_platform"] == "Linux/amd64"
    )


def test_capsule_evidence_keeps_complete_inventory_and_native_task_user_controls() -> None:
    report = json.loads((EVIDENCE / "review.json").read_bytes())
    for name, expected in report["artifacts"].items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == expected
    proposal = ROOT / report["proposal"]["path"]
    assert hashlib.sha256(proposal.read_bytes()).hexdigest() == report["proposal"]["sha256"]
    result = json.loads((EVIDENCE / "result.json").read_bytes())
    receipt = json.loads((EVIDENCE / "sdk-inventory.json").read_bytes())
    rows = receipt["inventory"]
    assert len(rows) == len({row["path"] for row in rows}) == result["observation"]["sdk_objects"]
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(raw).hexdigest() == receipt["inventory_sha256"] == result["complete_inventory_sha256"]
    assert receipt["archive_sha256"] == result["archive_sha256"]
    assert receipt["wrong_digest_rejected_before_extraction"] is True
    assert receipt["setup_uid"] == 0 and result["observation"]["task_uid"] != 0
    for row in rows:
        assert row["uid"] == row["gid"] == 0
        if row["kind"] != "symlink":
            assert row["mode"] & 0o222 == 0
    cases = {row["case"]: row for row in result["observation"]["cases"]}
    assert len(cases) == len(result["observation"]["cases"]) == 11
    for name in ("sdk-write-open-rejected", "sdk-mode-change-rejected", "sdk-new-file-rejected"):
        assert cases[name]["rejected"] is True
    assert cases["base-node-unchanged"]["version"] == "v20.20.0"
    assert cases["sdk-node-version"]["version"] == "v22.23.5"
    assert cases["npm-child-uses-capsule"]["major"] == 22
    assert cases["wrong-major-rejected"]["exit_code"] != 0
    assert cases["task-output-remains-writable"]["created"] is True
    assert cases["complete-sdk-unchanged-after-task-use"]["inventory_sha256"] == receipt["inventory_sha256"]
    assert report["node_capsule"]["fresh_repetitions"] == 2
    assert report["node_capsule"]["byte_identical_inventory_receipts"] is True
    assert result["lease_closed"] is True and result["remaining_owned_containers"] == 0
    assert result["runtime_admitted"] is False and result["model_invocations"] == 0
    assert report["execution_admitted"] is False and report["agent_efficacy_established"] is False
