"""Native benchmark controls must expose misses and reject evidence contamination."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
import report_workflow_evaluator_controls as controls


@pytest.fixture
def bundle():
    return json.loads((controls.EVIDENCE / "bundle.json").read_bytes())


def recapture(record, value):
    text = json.dumps(value, indent=2) + "\n"
    raw = text.encode("utf-8")
    record.update(utf8=text, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def test_real_controls_preserve_blind_spots_and_every_diagnostic(bundle):
    result = controls.inspect(bundle)
    assert result["ok"], result["errors"]
    for variant in result["variants"]:
        assert variant["tools"]["actionlint"]["missed_hazards"] == ["environment-fed-eval", "checkout-mutable-ref"]
        assert variant["tools"]["zizmor"]["missed_hazards"] == ["environment-fed-eval"]
        assert not any(tool["qualified_as_complete_security_grader"] for tool in variant["tools"].values())
    first_eval = next(row for row in result["variants"][0]["cases"] if row["case_id"] == "environment-fed-eval")
    assert first_eval["native"]["zizmor"]["all_rules"] == ["anonymous-definition"]
    assert not first_eval["native"]["zizmor"]["target_hazard_detected"]
    assert not result["agent_efficacy_scored"]
    assert not result["quality_superiority_claim_permitted"]


@pytest.mark.parametrize("location", ["definition", "execution", "workflow", "stdout", "stderr", "version", "license"])
def test_changed_native_capture_is_rejected(bundle, location):
    variant = bundle["variants"][0]
    records = {
        "definition": variant["definition"],
        "execution": variant["execution"],
        "workflow": variant["cases"][0]["workflow"],
        "stdout": variant["cases"][0]["native_outputs"]["zizmor"]["stdout"],
        "stderr": variant["cases"][0]["native_outputs"]["zizmor"]["stderr"],
        "version": bundle["tools"]["actionlint"]["version_output"],
        "license": bundle["tools"]["zizmor"]["license"],
    }
    records[location]["utf8"] += " "
    assert not controls.inspect(bundle)["ok"]


@pytest.mark.parametrize(
    "scope", ["workflow_execution_performed", "new_agent_calls_performed", "agent_efficacy_scored"]
)
def test_unmeasured_agent_or_execution_claim_is_rejected(bundle, scope):
    bundle[scope] = True
    assert not controls.inspect(bundle)["ok"]


def test_all_missing_control_errors_are_collected(bundle):
    for variant in bundle["variants"]:
        variant["cases"] = [row for row in variant["cases"] if row["id"] != "environment-fed-eval"]
    result = controls.inspect(bundle)
    assert not result["ok"]
    assert len(result["errors"]) == 2


def test_reclassifying_missed_hazard_as_safe_is_rejected(bundle):
    variant = bundle["variants"][0]
    definition = json.loads(variant["definition"]["utf8"])
    definition["cases"][4]["domain_expected_unsafe"] = False
    recapture(variant["definition"], definition)
    execution = json.loads(variant["execution"]["utf8"])
    execution["definition_sha256"] = variant["definition"]["sha256"]
    recapture(variant["execution"], execution)
    result = controls.inspect(bundle)
    assert not result["ok"]
    assert any("ground truth" in error for error in result["errors"])


def test_second_revision_cannot_fix_unsafe_control_to_manufacture_a_pass(bundle):
    variant = bundle["variants"][1]
    case = variant["cases"][4]
    text = case["workflow"]["utf8"].replace('eval "$PR_TITLE"', "printf '%s\\n' \"$PR_TITLE\"")
    assert text != case["workflow"]["utf8"]
    raw = text.encode("utf-8")
    case["workflow"].update(utf8=text, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    definition = json.loads(variant["definition"]["utf8"])
    definition["cases"][4]["input_sha256"] = case["workflow"]["sha256"]
    recapture(variant["definition"], definition)
    execution = json.loads(variant["execution"]["utf8"])
    execution["definition_sha256"] = variant["definition"]["sha256"]
    execution["cases"][4]["input_sha256"] = case["workflow"]["sha256"]
    recapture(variant["execution"], execution)
    result = controls.inspect(bundle)
    assert not result["ok"]
    assert any("changed more than" in error for error in result["errors"])


@pytest.mark.parametrize("mutation", ["exit", "ignore", "foreign-location", "suppression", "count"])
def test_resealed_invalid_run_or_diagnostic_is_rejected(bundle, mutation):
    variant = bundle["variants"][0]
    execution = json.loads(variant["execution"]["utf8"])
    native = execution["cases"][0]["zizmor"]
    output = variant["cases"][0]["native_outputs"]["zizmor"]["stdout"]
    diagnostics = json.loads(output["utf8"])
    if mutation == "exit":
        native["exit_code"] = 1
    elif mutation == "ignore":
        diagnostics[0]["ignored"] = True
    elif mutation == "foreign-location":
        diagnostics[0]["locations"][0]["symbolic"]["key"]["Local"]["verbatim_path"] = "other.yml"
    elif mutation == "suppression":
        native["command"].insert(1, "--min-severity=high")
    else:
        native["diagnostic_count"] += 1
    recapture(output, diagnostics)
    native["output_sha256"] = output["sha256"]
    recapture(variant["execution"], execution)
    assert not controls.inspect(bundle)["ok"]


def test_cli_checks_without_running_providers_and_rejects_report_tampering(tmp_path: Path, bundle, capsys):
    (tmp_path / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    args = ["--evidence-dir", str(tmp_path), "--json"]
    assert controls.main(args) == 0
    assert controls.main([*args, "--check"]) == 0
    report = json.loads((tmp_path / "report.json").read_bytes())
    report["variants"][1]["tools"]["zizmor"]["qualified_as_complete_security_grader"] = True
    (tmp_path / "report.json").write_text(json.dumps(report), encoding="utf-8")
    assert controls.main([*args, "--check"]) == 1
    assert "differs" in capsys.readouterr().out


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_regeneration_preserves_equivalent_evidence_bytes(tmp_path: Path, bundle, newline, capsys):
    (tmp_path / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    output = tmp_path / "report.json"
    text = json.dumps(controls.inspect(bundle), indent=2) + "\n"
    original = text.replace("\n", newline).encode("utf-8")
    output.write_bytes(original)
    assert controls.main(["--evidence-dir", str(tmp_path)]) == 0
    assert output.read_bytes() == original


def test_new_report_has_portable_utf8_lf_bytes(tmp_path: Path, bundle, capsys):
    (tmp_path / "bundle.json").write_text(json.dumps(bundle), encoding="utf-8")
    assert controls.main(["--evidence-dir", str(tmp_path)]) == 0
    raw = (tmp_path / "report.json").read_bytes()
    assert b"\r" not in raw
    assert json.loads(raw) == controls.inspect(bundle)


@pytest.mark.parametrize("value", [None, {}, [], {"schema_version": True}])
def test_invalid_envelopes_fail_closed(value):
    assert not controls.inspect(copy.deepcopy(value))["ok"]
