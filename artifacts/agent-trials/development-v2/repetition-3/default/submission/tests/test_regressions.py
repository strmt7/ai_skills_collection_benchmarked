"""Regression checks for schema validation, domain checks, and CLI verdicts."""

import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_benchmark_artifact", ROOT / "tools" / "check_benchmark_artifact.py"
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        # Keep every generated fixture inside the task workspace.
        self.temp = tempfile.TemporaryDirectory(prefix="artifact-regression-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.artifact_path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        self.schema = validator.load_json(validator.SCHEMA_PATH)
        self.artifact = copy.deepcopy(self.schema["examples"][0])
        self.write_json(self.catalog_path, [{
            "id": self.artifact["skill_id"],
            "commit_sha": self.artifact["source_commit"],
            "source_repo": self.artifact["source_repo"],
            "source_path": self.artifact["source_path"],
            "benchmark_scenarios": [self.artifact["scenario_id"]],
        }])
        self.write_json(self.scenarios_path, [{
            "id": self.artifact["scenario_id"],
            "dataset_track_id": "source-skill-repository",
        }])
        (self.base / "transcript.txt").write_text("recorded commands\n", encoding="utf-8")
        self.write_json(self.base / "result.json", {"recorded": True})
        (self.base / "screenshot.png").write_bytes(b"recorded screenshot fixture")
        (self.base / "directory").mkdir()

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=None):
        self.write_json(self.artifact_path, self.artifact if artifact is None else artifact)
        return validator.validate_artifact(
            self.artifact_path, self.catalog_path, self.scenarios_path
        )

    def assert_rejected(self, result, diagnostic=None):
        self.assertIn(result["verdict"], ("artifact_invalid", "artifact_incomplete"))
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if diagnostic:
            self.assertTrue(
                any(diagnostic in error for error in result["errors"]), result["errors"]
            )

    def enable_visual(self):
        self.artifact["scenario_requirements"]["visual_or_browser"] = True
        self.artifact["evidence"]["visual"] = {
            "screenshot_paths": ["screenshot.png"],
            "website_url_or_mirror": "https://example.invalid/recorded",
            "viewport": {"width": 1280, "height": 720},
        }

    def enable_memory(self):
        self.artifact["scenario_requirements"]["context_memory"] = True
        self.artifact["evidence"]["context_memory"] = {
            "delayed_recall_probes": [{"expected": "recorded", "actual": "recorded"}],
            "token_usage_before": 100,
            "token_usage_after": 80,
        }

    def test_complete_provenance_with_permitted_metadata(self):
        self.artifact["recording_metadata"] = {"nested": [None, {"detail": True}]}
        for name in ("runner", "input_snapshot", "execution", "evidence", "independence"):
            self.artifact[name]["extra"] = {"custom": [1, 2, 3]}
        self.artifact["metrics"]["verdict"] = "recorded"
        self.artifact["outputs"]["payload"] = {"arbitrary": True}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["warnings"])

    def test_complete_independent_recorded_artifact(self):
        self.artifact["artifact_kind"] = "independent_benchmark"
        self.artifact["independence"].update({
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
        })
        self.write_json(self.scenarios_path, [{
            "id": self.artifact["scenario_id"], "dataset_track_id": "external-fixture"
        }])
        self.enable_visual()
        self.enable_memory()
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_complete_record_against_bundled_catalog_and_scenarios(self):
        skill = validator.load_json(ROOT / "data" / "skills_catalog.json")[0]
        self.artifact.update({
            "skill_id": skill["id"], "scenario_id": skill["benchmark_scenarios"][0],
            "source_commit": skill["commit_sha"], "source_repo": skill["source_repo"],
            "source_path": skill["source_path"],
        })
        self.write_json(self.artifact_path, self.artifact)
        result = validator.validate_artifact(self.artifact_path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_malformed_top_level_fields_return_structured_verdicts(self):
        # Includes unhashable IDs/kinds and the input_snapshot.get crash.
        for key in self.schema["required"]:
            for value in (None, [], {}, True, 42, "unexpected"):
                if validator._matches_type(value, self.schema["properties"][key]["type"]):
                    continue
                with self.subTest(key=key, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    artifact[key] = value
                    self.assert_rejected(self.validate(artifact), "/" + key)

    def test_nested_types_and_required_fields(self):
        for section, definition in self.schema["properties"].items():
            for key, property_schema in definition.get("properties", {}).items():
                with self.subTest(section=section, key=key, case="wrong type"):
                    artifact = copy.deepcopy(self.artifact)
                    artifact[section][key] = None
                    self.assert_rejected(self.validate(artifact), f"/{section}/{key}")
            for key in definition.get("required", []):
                with self.subTest(section=section, key=key, case="missing"):
                    artifact = copy.deepcopy(self.artifact)
                    del artifact[section][key]
                    self.assert_rejected(self.validate(artifact), f"/{section}/{key}")

    def test_every_declared_min_length_is_enforced(self):
        def constrained_paths(schema, path=()):
            if "minLength" in schema:
                yield path
            for key, child in schema.get("properties", {}).items():
                yield from constrained_paths(child, path + (key,))
            if "items" in schema:
                yield from constrained_paths(schema["items"], path + (0,))

        for path in constrained_paths(self.schema):
            with self.subTest(path=path):
                artifact = copy.deepcopy(self.artifact)
                parent = artifact
                for key in path[:-1]:
                    parent = parent[key]
                parent[path[-1]] = ""
                self.assert_rejected(self.validate(artifact), "/" + "/".join(map(str, path)))

    def test_enum_pattern_and_array_constraints(self):
        cases = [
            ("artifact_version", "2.0"), ("artifact_kind", "other"),
            ("catalog_commit", "A" * 40), ("source_commit", "a" * 39),
            ("objective_checks", []), ("objective_checks", [12]),
        ]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                artifact = copy.deepcopy(self.artifact)
                artifact[key] = value
                self.assert_rejected(self.validate(artifact), "/" + key)
        for key in ("artifact_paths", "citations_or_paths"):
            for value in ([], [12], [None], [{}]):
                with self.subTest(key=key, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    artifact["evidence"][key] = value
                    self.assert_rejected(self.validate(artifact), f"/evidence/{key}")

    def test_missing_top_level_field(self):
        del self.artifact["runner"]
        self.assert_rejected(self.validate(), "/runner")

    def test_schema_unavailable_or_malformed_rejects_complete_record(self):
        schema_path = self.base / "schema.json"
        for contents in (None, "{broken", "[]", "null"):
            with self.subTest(contents=contents):
                if contents is not None:
                    schema_path.write_text(contents, encoding="utf-8")
                with mock.patch.object(validator, "SCHEMA_PATH", schema_path):
                    self.assert_rejected(self.validate(), "schema")

    def test_transcript_evidence_and_screenshots_must_identify_files(self):
        self.enable_visual()
        fields = (
            ("execution", "commands_or_transcript_path"),
            ("evidence", "artifact_paths"),
            ("evidence", "visual", "screenshot_paths"),
        )
        for path in fields:
            for value in ("directory", str(self.base / "directory"), "missing.txt", "bad\u0000path"):
                with self.subTest(path=path, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    parent = artifact
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = [value] if path[-1].endswith("paths") else value
                    result = self.validate(artifact)
                    self.assertEqual(result["verdict"], "artifact_incomplete", result)
                    self.assertTrue(result["errors"])

    def test_absolute_and_repository_relative_files_are_accepted(self):
        self.artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        self.artifact["evidence"]["artifact_paths"] = [
            str(self.base / "result.json"), "evaluators/benchmark_run_artifact.schema.json"
        ]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_visual_and_memory_requirements_return_incomplete(self):
        for flag in ("visual_or_browser", "context_memory"):
            with self.subTest(flag=flag):
                artifact = copy.deepcopy(self.artifact)
                artifact["scenario_requirements"][flag] = True
                result = self.validate(artifact)
                self.assertEqual(result["verdict"], "artifact_incomplete", result)

    def test_memory_token_counts_reject_booleans_and_malformed_values(self):
        self.enable_memory()
        for key in ("token_usage_before", "token_usage_after"):
            for value in (True, False, None, [], {}, "100", 0, -1, 1.5):
                with self.subTest(key=key, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    artifact["evidence"]["context_memory"][key] = value
                    self.assert_rejected(self.validate(artifact), "positive integer")

    def test_memory_increase_requires_numeric_quality_delta(self):
        self.enable_memory()
        self.artifact["evidence"]["context_memory"]["token_usage_after"] = 120
        for value in (None, True, "improved", [], {}):
            with self.subTest(value=value):
                self.artifact["evidence"]["context_memory"]["quality_delta"] = value
                self.assert_rejected(self.validate(), "quality_delta")
        self.artifact["evidence"]["context_memory"]["quality_delta"] = 0.5
        self.assertEqual(self.validate()["verdict"], "artifact_complete")
        self.artifact["scenario_requirements"]["token_efficiency_claim"] = True
        self.assert_rejected(self.validate(), "token_efficiency_claim")

    def test_domain_invariants_remain_enforced(self):
        cases = [
            ("benchmark_status", "passed"), ("verdict", "passed"),
            ("skill_id", "unknown"), ("scenario_id", "unknown"),
            ("source_repo", "other/repo"), ("source_path", "other.md"),
            ("source_commit", "f" * 40), ("artifact_kind", "independent_benchmark"),
        ]
        for key, value in cases:
            with self.subTest(key=key):
                artifact = copy.deepcopy(self.artifact)
                artifact[key] = value
                self.assert_rejected(self.validate(artifact))

    def test_invalid_json_and_non_object_roots(self):
        for contents in ("{", "null", "[]", "true", '"text"'):
            with self.subTest(contents=contents):
                self.artifact_path.write_text(contents, encoding="utf-8")
                result = validator.validate_artifact(self.artifact_path)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assertTrue(result["errors"])

    def test_cli_structured_output_and_exit_codes(self):
        for mutation, expected in ((None, 0), ("type", 1), ("missing file", 2)):
            with self.subTest(mutation=mutation):
                artifact = copy.deepcopy(self.artifact)
                if mutation == "type":
                    artifact["skill_id"] = []
                elif mutation == "missing file":
                    artifact["execution"]["commands_or_transcript_path"] = "absent.txt"
                self.write_json(self.artifact_path, artifact)
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = validator.main([
                        str(self.artifact_path), "--catalog", str(self.catalog_path),
                        "--scenarios", str(self.scenarios_path),
                    ])
                self.assertEqual(exit_code, expected)
                self.assertIn("verdict", json.loads(output.getvalue()))

    def test_batch_continues_after_malformed_record(self):
        self.artifact["skill_id"] = []
        self.write_json(self.artifact_path, self.artifact)
        second = self.base / "complete"
        second.mkdir()
        complete = copy.deepcopy(self.schema["examples"][0])
        complete["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        complete["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
        self.write_json(second / "artifact.json", complete)
        total, failed, failures = validator._validate_all(
            self.base, self.catalog_path, self.scenarios_path
        )
        self.assertEqual((total, failed), (2, 1))
        self.assertEqual(failures[0][0], self.artifact_path)


class SchemaWalkerTests(unittest.TestCase):
    def test_additional_properties_and_pointer_escaping(self):
        schema = {
            "type": "object", "properties": {"allowed": {"type": "string"}},
            "additionalProperties": False,
        }
        errors = []
        validator._schema_walk(schema, {"allowed": "yes", "extra/~": 1}, [], errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("/extra~1~0", errors[0])
        schema["additionalProperties"] = {"type": "integer"}
        errors = []
        validator._schema_walk(schema, {"count": "wrong"}, [], errors)
        self.assertTrue(any("/count" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
