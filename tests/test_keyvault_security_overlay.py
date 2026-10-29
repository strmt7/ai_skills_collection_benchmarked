"""Run source-bound Java examples with fake secrets and no Azure access."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import build_catalog
import check_keyvault_security_overlay as overlay
import pytest

CASES = (
    (
        "latest_secret",
        "SKILL.md",
        75,
        77,
        'KeyVaultSecret secret = secretClient.getSecret("database-password");\nString value = secret.getValue();\n// Use the value only for its intended operation; never print or log it.',
        None,
        "full",
    ),
    (
        "partial_value",
        "SKILL.md",
        119,
        120,
        '        KeyVaultSecret fullSecret = secretClient.getSecret(secretProps.getName());\n        System.out.println("Secret retrieved.");',
        None,
        "prefix",
    ),
    (
        "async_secret",
        "SKILL.md",
        209,
        210,
        'asyncClient.getSecret("async-secret")\n    .subscribe(secret -> System.out.println("Secret retrieved."));',
        None,
        "full",
    ),
    (
        "error_handling",
        "SKILL.md",
        278,
        279,
        '    KeyVaultSecret secret = secretClient.getSecret("my-secret");\n    System.out.println("Secret retrieved.");',
        None,
        "full",
    ),
    ("simple_create", "references/examples.md", 69, 70, 'System.out.println("Secret created.");', "secret", "full"),
    (
        "object_create",
        "references/examples.md",
        83,
        84,
        'System.out.println("Secret created.");',
        "returnedSecret",
        "full",
    ),
    ("get_current", "references/examples.md", 106, 107, 'System.out.println("Secret retrieved.");', "secret", "full"),
    (
        "get_version",
        "references/examples.md",
        115,
        116,
        'System.out.println("Secret retrieved.");',
        "secretWithVersion",
        "full",
    ),
    (
        "list_current",
        "references/examples.md",
        146,
        148,
        '    System.out.println("Secret retrieved.");',
        "secretWithValue",
        "full",
    ),
    (
        "list_version",
        "references/examples.md",
        178,
        180,
        '    System.out.println("Secret version retrieved.");',
        "secret",
        "full",
    ),
    (
        "async_get",
        "references/examples.md",
        298,
        302,
        'secretAsyncClient.getSecret("secretName")\n    .subscribe(\n        secret -> System.out.println("Secret retrieved."),\n        error -> System.err.println("Error: " + error.getMessage())\n    );',
        None,
        "full",
    ),
    (
        "update_chain",
        "references/examples.md",
        338,
        338,
        '        System.out.println("Secret retrieved.");',
        "retrieved",
        "full",
    ),
)
JAVA_PREFIX = """import java.util.function.Consumer;
public class Control {
 static final class KeyVaultSecret {
  String getValue(){return System.getenv("TRIAGE_SYNTHETIC_VALUE");}
  String getName(){return "fixture";}
 }
 static final class SecretClient { KeyVaultSecret getSecret(String ignored){return new KeyVaultSecret();} }
 static final class SecretProperties { String getName(){return "fixture";} String getVersion(){return "fixture-version";} }
 static final class Mono {
  void subscribe(Consumer<KeyVaultSecret> ok){ok.accept(new KeyVaultSecret());}
  void subscribe(Consumer<KeyVaultSecret> ok, Consumer<Throwable> err){ok.accept(new KeyVaultSecret());}
 }
 static final class AsyncClient { Mono getSecret(String ignored){return new Mono();} }
 public static void main(String[] args) {
  SecretClient secretClient=new SecretClient(); SecretProperties secretProps=new SecretProperties();
  AsyncClient asyncClient=new AsyncClient(); AsyncClient secretAsyncClient=new AsyncClient();
"""


@pytest.fixture(scope="module")
def java_tools():
    javac = shutil.which("javac")
    if not javac:
        pytest.skip("JDK is unavailable; the external Java control remains separately recorded")
    compiler = Path(javac).resolve()
    runtime = compiler.with_name("java.exe" if os.name == "nt" else "java")
    if not runtime.is_file():
        pytest.skip("Java runtime matching javac is unavailable")
    return compiler, runtime


def run_java(java_tools, folder: Path, snippet: str, receiver: str | None) -> bytes:
    compiler, runtime = java_tools
    folder.mkdir()
    declaration = "" if receiver is None else f"KeyVaultSecret {receiver}=new KeyVaultSecret();"
    source = folder / "Control.java"
    source.write_bytes((JAVA_PREFIX + declaration + "\n" + snippet + "\n }\n}\n").encode("utf-8"))
    env = dict(os.environ, TRIAGE_SYNTHETIC_VALUE="SYNTHETIC-ONLY-MARKER-947165")
    subprocess.run(
        [str(compiler), "-encoding", "UTF-8", str(source)], check=True, capture_output=True, env=env, timeout=30
    )
    result = subprocess.run(
        [str(runtime), "-cp", str(folder), "Control"], check=True, capture_output=True, env=env, timeout=30
    )
    return result.stdout + result.stderr


@pytest.mark.parametrize("name,relative,start,end,repaired,receiver,kind", CASES)
def test_repaired_examples_do_not_emit_secret_values(
    java_tools, tmp_path, name, relative, start, end, repaired, receiver, kind
):
    original_text = (overlay.ROOT / overlay.MIRROR / relative).read_text(encoding="utf-8")
    original = "\n".join(original_text.splitlines()[start - 1 : end])
    repaired_text = (overlay.ROOT / overlay.OVERLAY / relative).read_text(encoding="utf-8")
    assert repaired in repaired_text
    before = run_java(java_tools, tmp_path / "original", original, receiver)
    after = run_java(java_tools, tmp_path / "repaired", repaired, receiver)
    marker = b"SYNTHETIC-ONLY-MARKER-947165"
    assert (marker if kind == "full" else marker[:5]) in before
    assert marker[:5] not in after


def test_recorded_controls_match_independent_cases():
    report = json.loads((overlay.ROOT / overlay.CONTROL).read_text(encoding="utf-8"))
    assert report["baseline_verdict"] == "failed"
    assert report["repair_verdict"] == "passed"
    assert len(report["controls"]) == len(CASES)
    for recorded, (name, relative, start, end, _, _, _) in zip(report["controls"], CASES, strict=True):
        assert (
            recorded["case"],
            recorded["source_file"],
            recorded["source_start_line"],
            recorded["source_end_line"],
        ) == (name, relative, start, end)
        assert recorded["baseline_emitted_synthetic_value_or_prefix"] is True
        assert recorded["repair_emitted_synthetic_value_or_prefix"] is False


def test_java_literal_secret_inputs_are_marked_as_placeholders():
    # The checks inspect Java fenced blocks only; this is not a general Java taint analysis.
    ticks = chr(96) * 3
    fence = re.compile(r"^" + ticks + r"java[^\n]*\n(.*?)^" + ticks + r"[ \t]*(?:\n|$)", re.M | re.S)
    call = re.compile(
        r'\b(?:setSecret|new\s+KeyVaultSecret)\s*\(\s*"(?:\\.|[^"\\\r\n])*"\s*,\s*"((?:\\.|[^"\\\r\n])*)"',
        re.S,
    )
    for relative, expected_count in {
        "SKILL.md": 7,
        "references/examples.md": 5,
        "references/acceptance-criteria.md": 2,
    }.items():
        text = (overlay.ROOT / overlay.OVERLAY / relative).read_text(encoding="utf-8")
        values = [value for block in fence.finditer(text) for value in call.findall(block.group(1))]
        assert len(values) == expected_count
        assert all(value == "<secret-value>" for value in values)


def test_overlay_preserves_source_and_detects_drift(tmp_path):
    expected = overlay.expected_files()
    actual = overlay.ROOT / overlay.OVERLAY
    assert overlay.check_overlay(actual, expected) == []
    assert (actual / "provenance/original.SKILL.md").read_bytes() == build_catalog.sanitized_file_bytes(
        overlay.ROOT / overlay.MIRROR / "SKILL.md"
    )
    copied = tmp_path / "overlay"
    shutil.copytree(actual, copied)
    (copied / "references/examples.md").write_text("changed", encoding="utf-8")
    (copied / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    assert set(overlay.check_overlay(copied, expected)) == {
        "changed file: references/examples.md",
        "unexpected or missing file: unexpected.txt",
    }


@pytest.mark.skipif(os.name == "nt", reason="Windows executable modes are recorded in the Git index")
def test_checker_rejects_unexpected_executable_mode(tmp_path):
    files = overlay.expected_files()
    target = tmp_path / "mode-check"
    shutil.copytree(overlay.ROOT / overlay.OVERLAY, target)
    (target / "SKILL.md").chmod(0o755)
    assert overlay.check_overlay(target, files) == ["changed executable mode: SKILL.md"]


@pytest.mark.parametrize("change", ["missing_source", "duplicate_source", "missing_skill", "duplicate_skill"])
def test_source_lock_identity_must_be_unique_before_overlay(tmp_path, change):
    """Missing or ambiguous source identities must fail before mirror processing."""
    lock = json.loads((overlay.ROOT / "data/source_lock.json").read_text(encoding="utf-8"))
    (source,) = [item for item in lock["sources"] if item["repo"] == "microsoft/skills"]
    (entry,) = [item for item in source["skills"] if item["id"] == overlay.SKILL_ID]
    source["skills"] = [] if change == "missing_skill" else [entry, entry] if change == "duplicate_skill" else [entry]
    lock["sources"] = (
        [] if change == "missing_source" else [source, source] if change == "duplicate_source" else [source]
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data/source_lock.json").write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="one .* record"):
        overlay.expected_files(tmp_path)


@pytest.mark.parametrize(
    "field",
    [
        "skill_id",
        "source_commit",
        "source_skill_sha256",
        "source_tree_sha256",
        "source_examples_sha256",
        "baseline_verdict",
        "repair_verdict",
        "controls",
    ],
)
def test_every_control_identity_field_is_enforced(tmp_path, monkeypatch, field):
    """Each source and control field must reject independent tampering."""
    report = json.loads((overlay.ROOT / overlay.CONTROL).read_text(encoding="utf-8"))
    report[field] = [] if field == "controls" else "tampered"
    path = tmp_path / "control.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(overlay, "CONTROL", path)
    with pytest.raises(ValueError, match="control does not match"):
        overlay.expected_files()
