"""Offline external-vector, schema and source-example controls; no agent score."""

from __future__ import annotations

import ast
import base64
import copy
import io
import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stdout
from importlib.metadata import version
from pathlib import Path

from cryptography.exceptions import InvalidSignature, InvalidTag
from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jsonschema import Draft7Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import Unresolvable
from referencing.jsonschema import DRAFT7

BASE = "https://wycheproof.invalid/schemas/"
ROOT = Path(__file__).parent


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON member")
        result[key] = value
    return result


def nonfinite(_):
    raise ValueError("nonfinite JSON number")


def load(path):
    return json.loads(path.read_text("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)


def unavailable(uri):
    raise ValueError("schema retrieval is offline: " + uri)


def validators(schema_directory=ROOT / "schemas"):
    formats = FormatChecker(formats=[])
    for name in ("Hex", "HexBytes", "Asn"):
        formats.checks(name)(
            lambda value: isinstance(value, str) and re.fullmatch(r"(?:[0-9a-fA-F]{2})*", value) is not None
        )
    formats.checks("Pem")(
        lambda value: (
            isinstance(value, str)
            and value.startswith("-----BEGIN PUBLIC KEY-----\n")
            and value.rstrip().endswith("-----END PUBLIC KEY-----")
        )
    )
    formats.checks("EcCurve")(lambda value: value == "edwards25519")
    registry = Registry(retrieve=unavailable)
    schemas = {}
    for path in sorted(schema_directory.glob("*.json")):
        schema = load(path)
        Draft7Validator.check_schema(schema)
        stack = [schema]
        while stack:
            item = stack.pop()
            if isinstance(item, dict):
                if "format" in item and item["format"] not in formats.checkers:
                    raise ValueError("unqualified schema format")
                stack.extend(item.values())
            elif isinstance(item, list):
                stack.extend(item)
        schemas[path.name] = schema
        registry = registry.with_resource(
            BASE + path.name, Resource.from_contents(schema, default_specification=DRAFT7)
        )
    if len(schemas) != 5:
        raise ValueError("schema closure is incomplete")
    return {name: Draft7Validator({"$ref": BASE + name}, registry=registry, format_checker=formats) for name in schemas}


def checked(data, algorithm, schema, validation):
    validation.validate(data)
    if data["algorithm"] != algorithm or data["schema"] != schema:
        raise ValueError("algorithm/schema mismatch")
    cases = [case for group in data["testGroups"] for case in group["tests"]]
    ids = [case["tcId"] for case in cases]
    if not cases or data["numberOfTests"] != len(cases) or len(set(ids)) != len(ids):
        raise ValueError("empty, count-inconsistent or duplicate-ID vector set")
    if any(type(identifier) is not int or identifier <= 0 for identifier in ids):
        raise ValueError("case IDs must be positive integers")
    return data


def verdict(expected, rejected, output=None, correct=None):
    if expected not in {"valid", "invalid", "acceptable"}:
        raise ValueError("unknown result policy")
    if expected == "invalid":
        return rejected
    if rejected:
        return expected == "acceptable"
    return output == correct


def decrypt(cipher, nonce, ciphertext, aad):
    try:
        return False, cipher.decrypt(nonce, ciphertext, aad)
    except InvalidTag:
        return True, None


def aes_cases(data):
    rows = []
    for group in data["testGroups"]:
        for case in group["tests"]:
            row = {"tcId": case["tcId"], "expected": case["result"], "operation": "authenticated-decryption"}
            material = {key: bytes.fromhex(case[key]) for key in ("key", "iv", "aad", "ct", "tag", "msg")}
            if len(material["key"]) * 8 != group["keySize"] or len(material["iv"]) * 8 != group["ivSize"]:
                raise ValueError("group/input bit-length mismatch")
            if not 8 <= len(material["iv"]) <= 128 or group["tagSize"] != 128:
                row.update(status="excluded", reason="AESGCM API domain: 8..128-byte nonce and 128-bit tag")
            else:
                rejected, output = decrypt(
                    AESGCM(material["key"]), material["iv"], material["ct"] + material["tag"], material["aad"]
                )
                row.update(
                    status="passed" if verdict(case["result"], rejected, output, material["msg"]) else "failed",
                    rejected=rejected,
                )
            rows.append(row)
    return rows


def ed_cases(data):
    rows = []
    for group in data["testGroups"]:
        raw = bytes.fromhex(group["publicKey"]["pk"])
        if group["publicKey"]["curve"] != "edwards25519" or group["publicKey"]["keySize"] != 255:
            raise ValueError("unsupported public key domain")
        public = Ed25519PublicKey.from_public_bytes(raw)
        jwk = group.get("publicKeyJwk")
        if jwk is not None:
            encoded = jwk["x"]
            if jwk["kty"] != "OKP" or jwk["crv"] != "Ed25519" or not re.fullmatch(r"[A-Za-z0-9_-]+", encoded):
                raise ValueError("unsupported or malformed JWK")
            decoded = base64.b64decode(encoded + "=" * (-len(encoded) % 4), altchars=b"-_", validate=True)
            if decoded != raw or base64.urlsafe_b64encode(raw).decode().rstrip("=") != encoded:
                raise ValueError("JWK representation disagrees")
        for key in (
            serialization.load_der_public_key(bytes.fromhex(group["publicKeyDer"])),
            serialization.load_pem_public_key(group["publicKeyPem"].encode()),
        ):
            if not isinstance(key, Ed25519PublicKey) or key.public_bytes_raw() != raw:
                raise ValueError("public key representations disagree")
        for case in group["tests"]:
            rejected = False
            try:
                public.verify(bytes.fromhex(case["sig"]), bytes.fromhex(case["msg"]))
            except InvalidSignature:
                rejected = True
            rows.append(
                {
                    "tcId": case["tcId"],
                    "expected": case["result"],
                    "operation": "signature-verification",
                    "status": "passed" if verdict(case["result"], rejected, None, None) else "failed",
                    "rejected": rejected,
                }
            )
    return rows


def expect_exception(action, kind):
    try:
        action()
    except kind:
        return
    raise AssertionError("expected failure was absent")


def source_functions(heading):
    text = (ROOT / "original-SKILL.md").read_text("utf-8")
    section = text.split(heading, 1)[1]
    match = re.search(r"```python\n(.*?)\n```", section, re.DOTALL)
    if match is None:
        raise ValueError("source block is absent")
    parsed = ast.parse(match.group(1))
    nodes = []
    for node in parsed.body:
        if isinstance(node, ast.FunctionDef):
            node.decorator_list = []
            nodes.append(node)
        elif isinstance(node, (ast.Import, ast.ImportFrom)) and not any(alias.name == "pytest" for alias in node.names):
            nodes.append(node)
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "original-source-example.py", "exec"), namespace)
    return namespace


def run(_):
    validation = validators()
    aes = checked(
        load(ROOT / "testvectors_v1/aes_gcm_test.json"),
        "AES-GCM",
        "aead_test_schema_v1.json",
        validation["aead_test_schema_v1.json"],
    )
    ed = checked(
        load(ROOT / "testvectors_v1/ed25519_test.json"),
        "EDDSA",
        "eddsa_verify_schema_v1.json",
        validation["eddsa_verify_schema_v1.json"],
    )
    checks = ["five_schema_resources_validate_offline", "selected_vector_structures_and_custom_formats_validate"]
    for name, mutation, expected in (
        ("declared_count_mismatch_fails", lambda d: d.update(numberOfTests=d["numberOfTests"] + 1), ValueError),
        ("empty_selection_fails", lambda d: d.update(numberOfTests=0, testGroups=[]), ValueError),
        (
            "duplicate_case_id_fails",
            lambda d: d["testGroups"][0]["tests"].append(copy.deepcopy(d["testGroups"][0]["tests"][0])),
            ValueError,
        ),
        (
            "unknown_result_fails_schema",
            lambda d: d["testGroups"][0]["tests"][0].update(result="unknown"),
            ValidationError,
        ),
        ("odd_hex_fails_custom_format", lambda d: d["testGroups"][0]["tests"][0].update(iv="f"), ValidationError),
        ("wrong_algorithm_fails", lambda d: d.update(algorithm="EDDSA"), ValueError),
    ):
        altered = copy.deepcopy(aes)
        mutation(altered)
        if name == "duplicate_case_id_fails":
            altered["numberOfTests"] += 1
        expect_exception(
            lambda altered=altered: checked(
                altered, "AES-GCM", "aead_test_schema_v1.json", validation["aead_test_schema_v1.json"]
            ),
            expected,
        )
        checks.append(name)
    expect_exception(lambda: load(ROOT / "missing-vectors.json"), FileNotFoundError)
    checks.append("missing_vector_file_fails")
    expect_exception(lambda: json.loads('{"numberOfTests":1,"numberOfTests":0}', object_pairs_hook=pairs), ValueError)
    checks.append("duplicate_json_member_fails")
    expect_exception(lambda: json.loads('{"numberOfTests":NaN}', parse_constant=nonfinite), ValueError)
    checks.append("nonfinite_json_fails")
    offline = Draft7Validator({"$ref": BASE + "missing.json"}, registry=Registry(retrieve=unavailable))
    expect_exception(lambda: offline.validate({}), Unresolvable)
    checks.append("unknown_schema_reference_fails_without_network_retrieval")
    with tempfile.TemporaryDirectory(prefix="wycheproof-schema-format-") as temporary:
        directory = Path(temporary)
        for path in (ROOT / "schemas").glob("*.json"):
            shutil.copyfile(path, directory / path.name)
        altered_schema = load(directory / "common.json")
        altered_schema["format"] = "UnknownHex"
        (directory / "common.json").write_text(json.dumps(altered_schema), encoding="utf-8")
        expect_exception(lambda: validators(directory), ValueError)
    checks.append("unknown_schema_format_fails_closed")
    assert verdict("acceptable", True) and verdict("acceptable", False, b"a", b"a")
    assert not verdict("acceptable", False, b"wrong", b"a")
    checks.append("acceptable_accept_and_reject_policies_require_correct_accepted_output")
    expect_exception(lambda: verdict("other", True), ValueError)
    checks.append("unknown_result_policy_fails")

    class Unexpected:
        def decrypt(self, *_):
            raise RuntimeError("injected provider failure")

    expect_exception(lambda: decrypt(Unexpected(), b"", b"", b""), RuntimeError)
    checks.append("unexpected_provider_failure_propagates")
    loader = source_functions("### Phase 2: Parse Test Vectors")["load_wycheproof_test_vectors"]
    with redirect_stdout(io.StringIO()) as missing_output:
        assert loader(str(ROOT / "missing-vectors.json")) == []
    checks.append("original_missing_file_loader_returns_empty_success_candidate")
    original_cases = loader(str(ROOT / "testvectors_v1/aes_gcm_test.json"))
    rejected_case = next(case for case in original_cases if case["result"] == "invalid")
    original_decrypt = source_functions("### Phase 3: Write Testing Harness")["test_decryption"]
    expect_exception(lambda: original_decrypt(rejected_case), NameError)
    checks.append("original_decryption_handler_uses_missing_InvalidTag")
    aes_rows = aes_cases(aes)
    ed_rows = ed_cases(ed)
    checks.extend(
        ("eligible_aes_gcm_vectors_execute_against_real_provider", "all_ed25519_vectors_execute_against_real_provider")
    )
    checks.append("all_ed25519_raw_der_pem_jwk_key_representations_agree")
    return {
        "checks": checks,
        "algorithms": {
            "AES-GCM": {
                "selected": len(aes_rows),
                "summary": dict(Counter(row["status"] for row in aes_rows)),
                "cases": aes_rows,
            },
            "EDDSA": {
                "selected": len(ed_rows),
                "summary": dict(Counter(row["status"] for row in ed_rows)),
                "cases": ed_rows,
            },
        },
        "provider_versions": {
            package: version(package)
            for package in (
                "cryptography",
                "cffi",
                "pycparser",
                "jsonschema",
                "referencing",
                "attrs",
                "rpds-py",
                "jsonschema-specifications",
            )
        },
        "openssl_version": backend.openssl_version_text(),
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "uid": os.getuid(),
        "agent_processes": 0,
        "acceptable_cases_in_real_selected_vectors": 0,
        "acceptable_policy_controls_are_synthetic": True,
        "original_missing_file_stdout": missing_output.getvalue(),
        "original_example_registration_removed_function_bodies_preserved": True,
    }
