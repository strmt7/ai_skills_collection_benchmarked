"""Regression checks for structured artifact validation and schema enforcement."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import check_benchmark_artifact as validator


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        # All test inputs and recorded files stay inside the task workspace.
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / "tests", prefix="artifact-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.artifact_path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        self.schema = validator.load_json(validator.SCHEMA_PATH)
        self.artifact = copy.deepcopy(self.schema["examples"][0])
        self.artifact["skill_id"] = "fixture-skill"
        self.artifact["scenario_id"] = "fixture-proof"
        self.write_json(self.catalog_path, [{
            "id": "fixture-skill",
            "commit_sha": self.artifact["source_commit"],
            "source_repo": self.artifact["source_repo"],
            "source_path": self.artifact["source_path"],
            "benchmark_scenarios": ["fixture-proof", "fixture-independent"],
        }])
        self.write_json(self.scenarios_path, [
            {"id": "fixture-proof", "dataset_track_id": "source-skill-repository"},
            {"id": "fixture-independent", "dataset_track_id": "external-fixture"},
        ])
        for name in ("transcript.txt", "result.json", "screenshot.png"):
            (self.base / name).write_text("recorded fixture evidence", encoding="utf-8")

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=None):
        self.write_json(self.artifact_path, self.artifact if artifact is None else artifact)
        return validator.validate_artifact(
            self.artifact_path, self.catalog_path, self.scenarios_path
        )

    def assert_rejected(self, result, diagnostic=None):
        self.assertIn(result["verdict"], {"artifact_invalid", "artifact_incomplete"})
        self.assertIsInstance(result["errors"], list)
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if diagnostic:
            self.assertTrue(any(diagnostic in error for error in result["errors"]), result)

    @staticmethod
    def set_field(artifact, path, value):
        target = artifact
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value

    @staticmethod
    def declared_fields(schema, path=()):
        """Exercise every typed field in the bundled schema, including items."""
        for name, field_schema in schema.get("properties", {}).items():
            field_path = path + (name,)
            yield field_path, field_schema
            yield from ArtifactValidationTests.declared_fields(field_schema, field_path)
            if "items" in field_schema:
                yield field_path + (0,), field_schema["items"]

    def test_complete_provenance_and_permitted_extra_metadata(self):
        self.artifact["custom_metadata"] = {"notes": [None, 7, {"nested": True}]}
        for name in ("runner", "scenario_requirements", "input_snapshot", "execution",
                     "outputs", "metrics", "independence", "evidence"):
            self.artifact[name]["extra_metadata"] = {"recorded": True}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("do not count" in warning for warning in result["warnings"]))

    def test_complete_independent_benchmark_with_visual_and_memory_evidence(self):
        self.artifact["artifact_kind"] = "independent_benchmark"
        self.artifact["scenario_id"] = "fixture-independent"
        self.artifact["independence"].update({
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
        })
        self.artifact["scenario_requirements"].update({
            "visual_or_browser": True, "context_memory": True, "token_efficiency_claim": True,
        })
        self.artifact["evidence"].update({
            "visual": {
                "screenshot_paths": ["screenshot.png"],
                "website_url_or_mirror": "local fixture",
                "viewport": {"width": 800, "height": 600},
            },
            "context_memory": {
                "delayed_recall_probes": [{"question": "fixture", "answer": "recorded"}],
                "token_usage_before": 100, "token_usage_after": 80,
            },
        })
        result = self.validate()
        self.assertEqual(result, {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_complete_record_matches_bundled_catalog_and_scenarios(self):
        catalog = validator.load_json(ROOT / "data" / "skills_catalog.json")
        scenarios = validator.load_json(ROOT / "data" / "benchmark_scenarios.json")
        scenario_ids = {entry["id"] for entry in scenarios}
        skill = next(entry for entry in catalog if any(
            scenario in scenario_ids for scenario in entry["benchmark_scenarios"]
        ))
        self.artifact.update({
            "skill_id": skill["id"],
            "scenario_id": next(s for s in skill["benchmark_scenarios"] if s in scenario_ids),
            "source_commit": skill["commit_sha"],
            "source_repo": skill["source_repo"],
            "source_path": skill["source_path"],
        })
        self.write_json(self.artifact_path, self.artifact)
        result = validator.validate_artifact(self.artifact_path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_malformed_field_types_never_crash(self):
        # Include unhashable identifiers/kinds and non-object input_snapshot,
        # which previously reached unsafe domain lookups and .get calls.
        wrong_types = {
            "object": [None, [], "wrong", True, 1],
            "array": [None, {}, "wrong", True, 1],
            "string": [None, {}, [], True, 1],
            "boolean": [None, {}, [], "true", 1],
        }
        for path, field_schema in self.declared_fields(self.schema):
            for value in wrong_types[field_schema["type"]]:
                with self.subTest(path=path, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    self.set_field(artifact, path, value)
                    self.assert_rejected(self.validate(artifact), validator._pointer(path))

    def test_min_length_enforced_for_every_declared_string(self):
        # Add the optional runner label so all string paths can be mutated.
        self.artifact["runner"]["batch_name"] = "fixture"
        for path, field_schema in self.declared_fields(self.schema):
            if "minLength" not in field_schema:
                continue
            with self.subTest(path=path):
                artifact = copy.deepcopy(self.artifact)
                self.set_field(artifact, path, "")
                self.assert_rejected(self.validate(artifact), validator._pointer(path))

    def test_optional_empty_string_without_min_length_is_allowed(self):
        self.artifact["runner"]["batch_name"] = ""
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_required_fields_report_precise_paths(self):
        for parent_path, schema in [((), self.schema)] + [
            (path, field_schema) for path, field_schema in self.declared_fields(self.schema)
            if "required" in field_schema
        ]:
            for name in schema["required"]:
                with self.subTest(path=parent_path + (name,)):
                    artifact = copy.deepcopy(self.artifact)
                    parent = artifact
                    for part in parent_path:
                        parent = parent[part]
                    del parent[name]
                    self.assert_rejected(self.validate(artifact),
                                         validator._pointer(parent_path + (name,)))

    def test_patterns_enum_and_min_items_are_enforced(self):
        cases = [
            (("artifact_version",), "2.0"),
            (("artifact_kind",), "passed"),
            (("catalog_commit",), "A" * 40),
            (("source_commit",), "0" * 39),
            (("objective_checks",), []),
            (("evidence", "artifact_paths"), []),
            (("evidence", "citations_or_paths"), []),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                artifact = copy.deepcopy(self.artifact)
                self.set_field(artifact, path, value)
                self.assert_rejected(self.validate(artifact), validator._pointer(path))

    def test_additional_properties_constraints_and_pointer_escaping(self):
        schema_path = self.base / "schema.json"
        for additional, extra_value, accepted in [
            (False, "value", False),
            ({"type": "string", "minLength": 1}, "", False),
            ({"type": "string", "minLength": 1}, "value", True),
            (True, {"anything": []}, True),
        ]:
            for parent in (None, "runner"):
                with self.subTest(additional=additional, parent=parent):
                    schema = copy.deepcopy(self.schema)
                    constrained = schema if parent is None else schema["properties"][parent]
                    constrained["additionalProperties"] = additional
                    self.write_json(schema_path, schema)
                    artifact = copy.deepcopy(self.artifact)
                    target = artifact if parent is None else artifact[parent]
                    target["extra/key~"] = extra_value
                    with patch.object(validator, "SCHEMA_PATH", schema_path):
                        result = self.validate(artifact)
                    if accepted:
                        self.assertEqual(result["verdict"], "artifact_complete", result)
                    else:
                        prefix = "" if parent is None else f"/{parent}"
                        self.assert_rejected(result, prefix + "/extra~1key~0")

    def test_unavailable_or_unusable_schema_rejects_record(self):
        schema_path = self.base / "unusable-schema.json"
        for contents in (None, "{broken", "null", "[]", "{}"):
            with self.subTest(contents=contents):
                if contents is not None:
                    schema_path.write_text(contents, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    self.assert_rejected(self.validate(), "schema")
        with patch.object(validator, "SCHEMA_PATH", self.base):
            self.assert_rejected(self.validate(), "schema")
        with patch.object(validator, "load_json", side_effect=[self.artifact, PermissionError("unreadable")]):
            self.assert_rejected(validator.validate_artifact(self.artifact_path), "schema")

    def test_directory_missing_and_unusable_paths_are_rejected(self):
        (self.base / "directory").mkdir()
        for value in ("directory", ".", str(self.base), "missing.txt", "bad\x00path"):
            for field in ("transcript", "evidence", "screenshot"):
                with self.subTest(value=value, field=field):
                    artifact = copy.deepcopy(self.artifact)
                    if field == "transcript":
                        artifact["execution"]["commands_or_transcript_path"] = value
                    elif field == "evidence":
                        artifact["evidence"]["artifact_paths"] = [value]
                    else:
                        artifact["scenario_requirements"]["visual_or_browser"] = True
                        artifact["evidence"]["visual"] = {
                            "screenshot_paths": [value], "website_url_or_mirror": "local",
                            "viewport": {},
                        }
                    self.assert_rejected(self.validate(artifact), {
                        "transcript": "transcript", "evidence": "evidence", "screenshot": "screenshot",
                    }[field])

    def test_absolute_and_repo_relative_files_are_accepted(self):
        for absolute in (True, False):
            with self.subTest(absolute=absolute):
                artifact = copy.deepcopy(self.artifact)
                def recorded(name):
                    path = self.base / name
                    return str(path if absolute else path.relative_to(ROOT))
                artifact["execution"]["commands_or_transcript_path"] = recorded("transcript.txt")
                artifact["evidence"]["artifact_paths"] = [recorded("result.json")]
                self.assertEqual(self.validate(artifact)["verdict"], "artifact_complete")

    def test_context_memory_nested_malformed_values_and_booleans(self):
        self.artifact["scenario_requirements"]["context_memory"] = True
        valid_memory = {
            "delayed_recall_probes": ["recorded probe"],
            "token_usage_before": 100, "token_usage_after": 80,
        }
        for field, value in [
            ("delayed_recall_probes", None), ("delayed_recall_probes", {}),
            ("delayed_recall_probes", []), ("token_usage_before", []),
            ("token_usage_before", True), ("token_usage_after", False),
            ("token_usage_after", "80"), ("token_usage_after", 0),
        ]:
            with self.subTest(field=field, value=value):
                memory = dict(valid_memory, **{field: value})
                self.artifact["evidence"]["context_memory"] = memory
                self.assert_rejected(self.validate(), "context/memory")
        self.artifact["evidence"]["context_memory"] = dict(
            valid_memory, token_usage_after=120, quality_delta=True
        )
        self.assert_rejected(self.validate(), "quality_delta")
        self.artifact["evidence"]["context_memory"]["quality_delta"] = 0.2
        self.assertEqual(self.validate()["verdict"], "artifact_complete")
        self.artifact["scenario_requirements"]["token_efficiency_claim"] = True
        self.assert_rejected(self.validate(), "token_efficiency_claim")

    def test_domain_independence_self_claims_and_cross_references(self):
        mutations = [
            (("benchmark_status",), "passed"), (("verdict",), "passed"),
            (("skill_id",), "unknown"), (("scenario_id",), "unknown"),
            (("source_commit",), "1" * 40), (("source_repo",), "different/repo"),
            (("source_commit",), "0" * 40 + "\n"),
            (("source_path",), "different.md"), (("execution", "fresh_session"), False),
            (("input_snapshot", "is_real"), False),
            (("artifact_kind",), "independent_benchmark"),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                artifact = copy.deepcopy(self.artifact)
                self.set_field(artifact, path, value)
                result = self.validate(artifact)
                self.assertEqual(result["verdict"], "artifact_incomplete", result)
                self.assert_rejected(result)

    def test_invalid_json_roots_and_unreadable_artifacts(self):
        for contents in ("{broken", "null", "[]", '"string"', "42", "true"):
            with self.subTest(contents=contents):
                self.artifact_path.write_text(contents, encoding="utf-8")
                result = validator.validate_artifact(self.artifact_path)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assert_rejected(result)
        for path in (self.base / "missing.json", self.base):
            self.assert_rejected(validator.validate_artifact(path), "cannot read")

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"),
             *map(str, args), "--catalog", str(self.catalog_path),
             "--scenarios", str(self.scenarios_path)],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )

    def test_cli_reports_structured_verdicts_and_exit_codes(self):
        for state, verdict, code in [
            ("complete", "artifact_complete", 0),
            ("malformed", "artifact_invalid", 1),
            ("missing-evidence", "artifact_incomplete", 2),
        ]:
            with self.subTest(state=state):
                artifact = copy.deepcopy(self.artifact)
                if state == "malformed":
                    artifact["skill_id"] = []
                elif state == "missing-evidence":
                    artifact["evidence"]["artifact_paths"] = ["missing.json"]
                self.write_json(self.artifact_path, artifact)
                process = self.cli(self.artifact_path)
                self.assertEqual(process.returncode, code, process.stderr)
                self.assertEqual(process.stderr, "")
                self.assertEqual(json.loads(process.stdout)["verdict"], verdict)

    def test_batch_validation_continues_after_malformed_record(self):
        self.validate()
        broken = self.base / "broken"
        broken.mkdir()
        artifact = copy.deepcopy(self.artifact)
        artifact["input_snapshot"] = []
        self.write_json(broken / "artifact.json", artifact)
        complete = self.base / "z-complete"
        complete.mkdir()
        artifact = copy.deepcopy(self.artifact)
        artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        artifact["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
        self.write_json(complete / "artifact.json", artifact)
        total, failed, failures = validator._validate_all(
            self.base, self.catalog_path, self.scenarios_path
        )
        self.assertEqual((total, failed), (3, 1))
        self.assertEqual(failures[0][0], broken / "artifact.json")
        process = self.cli("--validate-all", self.base)
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertIn("artifact_invalid", process.stderr)
        self.assertIn("/input_snapshot", process.stderr)
        self.assertNotIn("Traceback", process.stderr)
        (broken / "artifact.json").unlink()
        process = self.cli("--validate-all", self.base)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("validated 2", process.stdout)


if __name__ == "__main__":
    unittest.main()
