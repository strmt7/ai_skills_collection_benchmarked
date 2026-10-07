"""Run and independently crosscheck pinned external crypto-vector controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
PACKAGE = "included/skills/by-category/testing-qa-benchmarking/security-reference/wycheproof"
EXPECTED = {
    "five_schema_resources_validate_offline",
    "selected_vector_structures_and_custom_formats_validate",
    "declared_count_mismatch_fails",
    "empty_selection_fails",
    "duplicate_case_id_fails",
    "unknown_result_fails_schema",
    "odd_hex_fails_custom_format",
    "wrong_algorithm_fails",
    "missing_vector_file_fails",
    "duplicate_json_member_fails",
    "nonfinite_json_fails",
    "acceptable_accept_and_reject_policies_require_correct_accepted_output",
    "unknown_result_policy_fails",
    "unexpected_provider_failure_propagates",
    "original_missing_file_loader_returns_empty_success_candidate",
    "original_decryption_handler_uses_missing_InvalidTag",
    "eligible_aes_gcm_vectors_execute_against_real_provider",
    "all_ed25519_vectors_execute_against_real_provider",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--image-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    from isolated_python import IMAGE, run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    manifest_path = Path(__file__).with_name("wycheproof-inputs.json")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    image_bytes = args.image_receipt.read_bytes()
    preparation = json.loads(image_bytes)
    if not preparation.get("passed") or preparation.get("base_image") != IMAGE or preparation.get("inputs_manifest_sha256") != hashlib.sha256(manifest_bytes).hexdigest():
        raise ValueError("provider image is not qualified for these inputs")
    external_paths = []
    for name, resource in manifest["resources"].items():
        path = args.input_dir / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != resource["bytes"] or hashlib.sha256(path.read_bytes()).hexdigest() != resource["sha256"]:
            raise ValueError("external input is not the hash-qualified regular file")
        external_paths.append(path)
    original = ROOT / PACKAGE / "SKILL.md"
    fixture = Path(__file__).with_name("wycheproof_provider_fixture.py")
    project_hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in (original, fixture, manifest_path)}
    with tempfile.TemporaryDirectory(prefix="wycheproof-controls-") as temporary:
        stage = Path(temporary)
        shutil.copyfile(original, stage / "original-SKILL.md")
        shutil.copyfile(fixture, stage / "candidate.py")
        names = ["original-SKILL.md", "candidate.py"]
        for path in external_paths:
            name = path.relative_to(args.input_dir).as_posix()
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            names.append(name)
        invocation = run_isolated(stage, names, {}, image=preparation["image"], timeout=40)
    result = invocation.get("candidate_response", {}).get("result", {})
    errors = []
    if invocation["status"] != "completed" or not invocation["cleanup_verified"]:
        errors.append("isolated invocation did not complete with verified cleanup")
    if set(result.get("checks", [])) != EXPECTED or len(result.get("checks", [])) != len(EXPECTED):
        errors.append("not all source/schema controls completed")
    expected_counts = {}
    for filename, algorithm in (("aes_gcm_test.json", "AES-GCM"), ("ed25519_test.json", "EDDSA")):
        data = json.loads((args.input_dir / "testvectors_v1" / filename).read_bytes())
        cases = [(group, case) for group in data["testGroups"] for case in group["tests"]]
        actual = result.get("algorithms", {}).get(algorithm, {})
        rows = actual.get("cases", [])
        by_id = {row["tcId"]: row for row in rows}
        excluded = 0
        if len(rows) != len(cases) or len(by_id) != len(rows) or set(by_id) != {case["tcId"] for _, case in cases}:
            errors.append(algorithm + " did not account for every selected case ID")
        for group, case in cases:
            eligible = algorithm == "EDDSA" or (64 <= group["ivSize"] <= 1024 and group["tagSize"] == 128)
            excluded += int(not eligible)
            row = by_id.get(case["tcId"], {})
            if row.get("expected") != case["result"] or row.get("status") != ("passed" if eligible else "excluded"):
                errors.append(algorithm + " case " + str(case["tcId"]) + " has a result/accounting mismatch")
            if not eligible and row.get("reason") != "AESGCM API domain: 8..128-byte nonce and 128-bit tag":
                errors.append("excluded case lacks the declared API-domain reason")
        expected_counts[algorithm] = {"selected": len(cases), "eligible": len(cases) - excluded, "excluded": excluded}
    for package, wheel in manifest["wheels"].items():
        if result.get("provider_versions", {}).get(package) != wheel["version"]:
            errors.append("runtime provider mismatch: " + package)
    if result.get("uid") != 65534 or result.get("platform") != "linux" or result.get("python_version") != "3.14.8" or result.get("agent_processes") != 0:
        errors.append("runtime platform/identity mismatch")
    for name, digest in project_hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("project source changed during controls")
    if args.image_receipt.read_bytes() != image_bytes:
        raise ValueError("image receipt changed during controls")
    for name, resource in manifest["resources"].items():
        if hashlib.sha256((args.input_dir / name).read_bytes()).hexdigest() != resource["sha256"]:
            raise ValueError("external input changed during controls")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-pinned-wycheproof-provider-schema-and-source-example-controls",
        "passed": not errors,
        "errors": errors,
        "project_file_sha256": project_hashes,
        "external_input_sha256": {name: resource["sha256"] for name, resource in manifest["resources"].items()},
        "image_preparation_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "independent_expected_counts": expected_counts,
        "expectations_from_external_vector_and_provider_contracts": True,
        "source_example_checks_are_provenance_controls_only": True,
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "constant_time_behavior_qualified": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": not errors, "errors": errors[:10], "counts": expected_counts, "status": invocation["status"], "response": invocation.get("candidate_response", {}) if errors else {"controls": len(result["checks"]), "openssl": result["openssl_version"]}}))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
