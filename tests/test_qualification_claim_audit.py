"""Keep retrospective fixture evidence, revoked claims and model admission separate."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "artifacts/research/2026-11-13/qualification-claim-audit"


def test_historical_claim_audit_preserves_failures_and_partial_scope() -> None:
    review = json.loads((FOLDER / "review.json").read_bytes())
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == digest
    audit = json.loads((FOLDER / "native-reconciliation.json").read_bytes())
    inventory = json.loads((FOLDER / "inventory-summary.json").read_bytes())
    assert audit["inventory_sha256"] == inventory["private_inventory_sha256"]
    assert inventory["qualification_files"] == review["inventory_qualification_files"] == 260
    assert inventory["schema_variants"] == review["inventory_schema_variants"] == 18
    counts = dict(Counter(row["classification"] for row in audit["records"]))
    assert counts == audit["classification_counts"] == review["classification_counts"]
    assert sum(counts.values()) == len(audit["records"]) == review["selected_native_controller_checks"] == 53
    assert review["all_legacy_qualification_artifacts_audited"] is False
    assert audit["all_legacy_qualification_artifacts_audited"] is False
    assert not review["current_model_execution_admitted"] and not audit["current_model_execution_admitted"]
    assert not review["model_improvement_established"] and review["new_model_invocations"] == 0
    for row in audit["records"]:
        classification = row["classification"]
        if classification == "native_command_and_original_grader_success_verified":
            assert row["native_command_count"] == 1 and row["native_command_exit_codes"] == [0]
            native = row["original_native_counts"]
            assert native["passed"] == native["total"]
            assert native["failed"] == native["skipped"] == native["errors"] == 0
            assert row["historical_scope_only"] and row["publisher_nonroot"]
            assert row["model_invocations"] == row["counted_attempts"] == 0
        elif classification == "tool_free_unchanged_failure_verified":
            assert row["native_command_count"] == 0 and row["native_command_exit_codes"] == []
            assert row["original_native_counts"]["passed"] == 0 and row["historical_task_status"] == "task_failed"
        elif classification == "historical_negative_claim_not_readmitted":
            assert row["negative_cause_audit_complete"] is False and row["historical_task_status"] == "harness_error"
        elif classification == "historical_failed_qualification_preserved":
            assert row["historical_check_passed"] is False
        else:
            assert classification == "revoked_wrapper_pass_nested_summary_failed"
            assert row["historical_check_passed"] is True and row["nested_summary_passed"] is False
            assert not row["accepted_for_current_admission"] and not row["original_receipts_modified"]
    revocations = json.loads((FOLDER / "revocations.json").read_bytes())
    assert len(revocations["new_revoked_historical_wrapper_claims"]) == 1
    assert not revocations["original_receipts_modified"] and not revocations["model_outcomes_removed_or_replaced"]
    for field in ("previous_marker_claim_revocations", "separate_metadata_scope_correction"):
        ref = revocations[field]
        assert hashlib.sha256((ROOT / ref["path"]).read_bytes()).hexdigest() == ref["sha256"]
