"""Behavioral regressions for benchmark artifact validation (no external data)."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_benchmark_artifact", ROOT / "tools" / "check_benchmark_artifact.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        # Keep all fixtures in the authorized task workspace, including CLI runs.
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.artifact_path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        for name in ("transcript.txt", "result.json", "screenshot.png"):
            (self.base / name).write_text("recorded evidence", encoding="utf-8")
        self.write_json(self.catalog_path, [{
            "id": "test-skill",
            "commit_sha": "a" * 40,
            "source_repo": "test/repository",
            "source_path": "skills/test/SKILL.md",
            "benchmark_scenarios": ["test-scenario", "source-proof"],
        }])
        self.write_json(self.scenarios_path, [
            {"id": "test-scenario", "dataset_track_id": "independent-fixture"},
            {"id": "source-proof", "dataset_track_id": "source-skill-repository"},
        ])
        self.artifact = {
            "artifact_version": "1.0",
            "artifact_kind": "independent_benchmark",
            "skill_id": "test-skill",
            "scenario_id": "test-scenario",
            "catalog_commit": "b" * 40,
            "source_commit": "a" * 40,
            "source_repo": "test/repository",
            "source_path": "skills/test/SKILL.md",
            "runner": {
                "timestamp_utc": "2026-10-02T12:00:00Z",
                "tool": "fixture-runner",
                "model_or_runtime": "recorded-runtime",
            },
            "scenario_requirements": {},
            "input_snapshot": {
                "kind": "fixture", "identifier": "fixture-v1", "is_real": True,
            },
            "execution": {
                "fresh_session": True,
                "commands_or_transcript_path": "transcript.txt",
            },
            "outputs": {"result": "result.json"},
            "metrics": {"accuracy": 1.0},
            "independence": {
                "task_defined_outside_skill": True,
                "evaluator_defined_outside_skill": True,
                "expected_result_defined_outside_skill": True,
                "uses_exact_skill_content_for_expected_result": False,
                "skill_content_usage": "instructions only",
            },
            "evidence": {
                "artifact_paths": ["result.json"],
                "citations_or_paths": ["https://example.invalid/fixture-v1"],
            },
            "objective_checks": ["accuracy"],
        }

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=None):
        self.write_json(self.artifact_path, self.artifact if artifact is None else artifact)
        return validator.validate_artifact(
            self.artifact_path, self.catalog_path, self.scenarios_path
        )

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], ("artifact_invalid", "artifact_incomplete"))
        self.assertIsInstance(result["errors"], list)
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(any(pointer in error for error in result["errors"]), result)

    def test_complete_record_and_extra_metadata_are_accepted(self):
        self.artifact["metadata"] = {"nested": [None, 42, {"note": "recorded"}]}
        self.artifact["runner"]["extra"] = {"batch": "trial"}
        self.artifact["evidence"]["annotations"] = ["recorded"]
        result = self.validate()
        self.assertEqual(result, {
            "verdict": "artifact_complete", "errors": [], "warnings": [],
        })

    def test_complete_provenance_is_accepted_with_warning(self):
        self.artifact["artifact_kind"] = "provenance_check"
        self.artifact["scenario_id"] = "source-proof"
        self.artifact["independence"].update({
            "task_defined_outside_skill": False,
            "expected_result_defined_outside_skill": False,
            "uses_exact_skill_content_for_expected_result": True,
            "skill_content_usage": "source provenance",
        })
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete")
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["warnings"])

    def test_malformed_top_level_values_never_crash(self):
        # Exercise every required field with JSON shapes that previously reached
        # unsafe dictionary lookups, set membership, and .get calls.
        for field in self.artifact:
            for value in (None, [], {}, 7, True, ""):
                if type(value) is type(self.artifact[field]):
                    continue
                with self.subTest(field=field, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    artifact[field] = value
                    self.assert_rejected(self.validate(artifact), "/" + field)

    def test_bundled_nonempty_strings_are_enforced(self):
        # Discover every declared minLength in the bundled schema, including
        # items and nested fields, rather than testing only domain-required text.
        schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))

        def string_paths(node, parts=()):
            if "minLength" in node:
                yield parts
            for key, child in node.get("properties", {}).items():
                yield from string_paths(child, parts + (key,))
            if "items" in node:
                yield from string_paths(node["items"], parts + (0,))

        for parts in string_paths(schema):
            with self.subTest(path=parts):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = ""
                self.assert_rejected(
                    self.validate(artifact), "/" + "/".join(map(str, parts))
                )

    def test_other_schema_constraints_and_nested_types(self):
        cases = [
            (("artifact_version",), "2.0"),
            (("artifact_kind",), "unknown"),
            (("source_commit",), "A" * 40),
            (("runner", "tool"), []),
            (("scenario_requirements", "visual_or_browser"), "true"),
            (("input_snapshot", "is_real"), 1),
            (("execution", "fresh_session"), 1),
            (("evidence", "artifact_paths"), []),
            (("evidence", "citations_or_paths"), [None]),
            (("evidence", "visual"), []),
            (("evidence", "context_memory"), False),
            (("objective_checks",), []),
            (("objective_checks",), [42]),
        ]
        for parts, value in cases:
            with self.subTest(path=parts, value=value):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = value
                self.assert_rejected(self.validate(artifact), "/" + "/".join(parts))

    def test_missing_required_fields_and_bad_json(self):
        for parts in (("outputs",), ("runner", "tool"), ("input_snapshot", "kind")):
            with self.subTest(path=parts):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                del target[parts[-1]]
                self.assert_rejected(self.validate(artifact), "/" + "/".join(parts))
        for text in ("{", "[]", "null"):
            with self.subTest(text=text):
                self.artifact_path.write_text(text, encoding="utf-8")
                result = validator.validate_artifact(self.artifact_path)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assert_rejected(result)

    def test_schema_unavailable_rejects_complete_record(self):
        schema_path = self.base / "unavailable-schema.json"
        for text in (None, "{", "[]", "null", "{}"):
            with self.subTest(schema_contents=text):
                if text is not None:
                    schema_path.write_text(text, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    result = self.validate()
                self.assert_rejected(result)
                self.assertTrue(any("schema" in error.lower() for error in result["errors"]))
        schema_path.unlink()
        schema_path.mkdir()
        with patch.object(validator, "SCHEMA_PATH", schema_path):
            self.assert_rejected(self.validate())

    def test_transcript_evidence_and_screenshots_must_be_files(self):
        directory = self.base / "evidence-directory"
        directory.mkdir()
        for path in ("evidence-directory", str(directory), "missing-file", "bad\x00path"):
            for location in ("transcript", "evidence", "screenshot"):
                with self.subTest(path=path, location=location):
                    artifact = copy.deepcopy(self.artifact)
                    if location == "transcript":
                        artifact["execution"]["commands_or_transcript_path"] = path
                    elif location == "evidence":
                        artifact["evidence"]["artifact_paths"] = [path]
                    else:
                        artifact["scenario_requirements"]["visual_or_browser"] = True
                        artifact["evidence"]["visual"] = {
                            "screenshot_paths": [path],
                            "website_url_or_mirror": "https://example.invalid",
                            "viewport": {"width": 1280, "height": 720},
                        }
                    self.assert_rejected(self.validate(artifact))

    def test_complete_visual_and_context_evidence_and_domain_failures(self):
        self.artifact["scenario_requirements"] = {
            "visual_or_browser": True, "context_memory": True,
            "token_efficiency_claim": True,
        }
        self.artifact["evidence"].update({
            "visual": {
                "screenshot_paths": ["screenshot.png"],
                "website_url_or_mirror": "https://example.invalid",
                "viewport": {"width": 1280, "height": 720},
            },
            "context_memory": {
                "delayed_recall_probes": ["recall-fixture"],
                "token_usage_before": 200, "token_usage_after": 100,
            },
        })
        self.assertEqual(self.validate()["verdict"], "artifact_complete")
        cases = [
            ("independence", "task_defined_outside_skill", False),
            ("execution", "fresh_session", False),
            ("input_snapshot", "is_real", False),
        ]
        for section, field, value in cases:
            with self.subTest(field=field):
                artifact = copy.deepcopy(self.artifact)
                artifact[section][field] = value
                self.assert_rejected(self.validate(artifact))
        self.artifact["evidence"]["context_memory"]["token_usage_after"] = 300
        self.assert_rejected(self.validate())

    def test_additional_properties_rules_in_schema_walker(self):
        schema = {
            "type": "object", "properties": {"known": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = []
        validator._schema_walk(schema, {"known": "ok", "a/b~c": 1}, [], errors)
        self.assertTrue(any("/a~1b~0c" in error for error in errors), errors)
        schema["additionalProperties"] = {"type": "string", "minLength": 1}
        errors = []
        validator._schema_walk(schema, {"extra": ""}, [], errors)
        self.assertTrue(any("/extra" in error for error in errors), errors)

    def test_relative_repo_paths_and_absolute_file_paths(self):
        repo = self.base / "repo"
        repo.mkdir()
        (repo / "recorded.txt").write_text("record", encoding="utf-8")
        self.artifact["execution"]["commands_or_transcript_path"] = "recorded.txt"
        self.artifact["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
        with patch.object(validator, "ROOT", repo):
            self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_cli_returns_json_and_exit_codes_without_tracebacks(self):
        malformed = copy.deepcopy(self.artifact)
        malformed["skill_id"] = []
        unknown = copy.deepcopy(self.artifact)
        unknown["skill_id"] = "unknown-skill"
        for artifact, expected_verdict in (
            (self.artifact, "artifact_complete"),
            (malformed, "artifact_incomplete"),
            (unknown, "artifact_incomplete"),
            ([], "artifact_invalid"),
        ):
            with self.subTest(artifact=artifact):
                self.write_json(self.artifact_path, artifact)
                result = subprocess.run([
                    sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"),
                    str(self.artifact_path), "--catalog", str(self.catalog_path),
                    "--scenarios", str(self.scenarios_path),
                ], capture_output=True, text=True, check=False)
                verdict = json.loads(result.stdout)
                expected_code = {
                    "artifact_complete": 0, "artifact_invalid": 1, "artifact_incomplete": 2,
                }[verdict["verdict"]]
                self.assertEqual(result.returncode, expected_code, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(verdict["verdict"], expected_verdict)
                if expected_verdict != "artifact_complete":
                    self.assert_rejected(verdict)

    def test_batch_validation_continues_after_a_malformed_record(self):
        batch = self.base / "batch"
        for name, malformed in (("a-malformed", True), ("b-complete", False)):
            record_dir = batch / name
            record_dir.mkdir(parents=True)
            artifact = copy.deepcopy(self.artifact)
            artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
            artifact["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
            if malformed:
                artifact["input_snapshot"] = None
            self.write_json(record_dir / "artifact.json", artifact)
        total, failed, failures = validator._validate_all(
            batch, self.catalog_path, self.scenarios_path
        )
        self.assertEqual((total, failed), (2, 1))
        self.assertEqual(failures[0][0].parent.name, "a-malformed")
        self.assert_rejected(failures[0][1], "/input_snapshot")
        result = subprocess.run([
            sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"),
            "--validate-all", str(batch), "--catalog", str(self.catalog_path),
            "--scenarios", str(self.scenarios_path),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("a-malformed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
