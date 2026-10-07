"""Regression coverage for benchmark artifact structure and evidence checks."""

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
spec = importlib.util.spec_from_file_location(
    "check_benchmark_artifact", ROOT / "tools" / "check_benchmark_artifact.py"
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ArtifactRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="artifact-tests-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.path = self.base / "artifact.json"
        self.schema = validator.load_json(validator.SCHEMA_PATH)
        self.catalog = validator.load_json(ROOT / "data" / "skills_catalog.json")
        self.scenarios = {
            item["id"]: item
            for item in validator.load_json(ROOT / "data" / "benchmark_scenarios.json")
        }
        skill = self.catalog[0]
        scenario_id = next(
            name for name in skill["benchmark_scenarios"]
            if self.scenarios[name].get("dataset_track_id") == "source-skill-repository"
        )
        self.artifact = copy.deepcopy(self.schema["examples"][0])
        self.artifact.update(
            skill_id=skill["id"],
            scenario_id=scenario_id,
            source_commit=skill["commit_sha"],
            source_repo=skill["source_repo"],
            source_path=skill["source_path"],
        )
        (self.base / "transcript.txt").write_text("recorded commands\n", encoding="utf-8")
        (self.base / "result.json").write_text('{"proof": true}', encoding="utf-8")
        (self.base / "screenshot.png").write_bytes(b"recorded screenshot")
        (self.base / "directory").mkdir()

    def validate(self, artifact=None):
        record = self.artifact if artifact is None else artifact
        self.path.write_text(json.dumps(record), encoding="utf-8")
        result = validator.validate_artifact(self.path)
        self.assertEqual(set(result), {"verdict", "errors", "warnings"})
        self.assertIsInstance(result["errors"], list)
        self.assertIsInstance(result["warnings"], list)
        return result

    def assert_rejected_at(self, artifact, parts):
        result = self.validate(artifact)
        self.assertEqual(result["verdict"], "artifact_invalid", result)
        pointer = "/" + "/".join(map(str, parts)) + ":"
        self.assertTrue(any(error.startswith(pointer) for error in result["errors"]), result)

    @staticmethod
    def schema_fields(schema, parts=()):
        for name, field in schema.get("properties", {}).items():
            field_parts = parts + (name,)
            yield field_parts, field
            yield from ArtifactRegressionTests.schema_fields(field, field_parts)

    @staticmethod
    def parent(record, parts):
        for name in parts[:-1]:
            record = record[name]
        return record

    def test_complete_provenance_and_permitted_metadata(self):
        self.artifact["extra_metadata"] = {"labels": ["recorded"], "optional": None}
        for parts, field in self.schema_fields(self.schema):
            if field.get("type") == "object":
                parent = self.parent(self.artifact, parts)
                parent.setdefault(parts[-1], {})["extra_metadata"] = {"value": [1, True]}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("do not count as runtime benchmark passes" in w for w in result["warnings"]))

    def test_complete_independent_record_with_visual_and_memory_evidence(self):
        skill = self.catalog[0]
        self.artifact["artifact_kind"] = "independent_benchmark"
        self.artifact["scenario_id"] = next(
            name for name in skill["benchmark_scenarios"]
            if self.scenarios[name].get("dataset_track_id") != "source-skill-repository"
        )
        self.artifact["independence"].update(
            task_defined_outside_skill=True,
            evaluator_defined_outside_skill=True,
            expected_result_defined_outside_skill=True,
            uses_exact_skill_content_for_expected_result=False,
        )
        self.artifact["scenario_requirements"].update(
            visual_or_browser=True, context_memory=True, token_efficiency_claim=True
        )
        self.artifact["evidence"].update(
            visual={
                "screenshot_paths": ["screenshot.png"],
                "website_url_or_mirror": "https://example.invalid/recorded",
                "viewport": {"width": 1280, "height": 720},
            },
            context_memory={
                "delayed_recall_probes": ["recorded probe"],
                "token_usage_before": 200,
                "token_usage_after": 100,
            },
        )
        result = self.validate()
        self.assertEqual(result, {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_wrong_types_for_every_schema_field_are_structured(self):
        wrong_values = {
            "object": [None, True, 1, "text", []],
            "string": [None, True, 1, [], {}],
            "array": [None, True, 1, "text", {}],
            "boolean": [None, 0, 1, "true", [], {}],
        }
        for parts, field in self.schema_fields(self.schema):
            for value in wrong_values[field["type"]]:
                with self.subTest(field=parts, value=value):
                    record = copy.deepcopy(self.artifact)
                    self.parent(record, parts)[parts[-1]] = value
                    self.assert_rejected_at(record, parts)

    def test_all_minimum_lengths_and_array_constraints(self):
        for parts, field in self.schema_fields(self.schema):
            if "minLength" in field:
                with self.subTest(field=parts, constraint="minLength"):
                    record = copy.deepcopy(self.artifact)
                    self.parent(record, parts)[parts[-1]] = ""
                    self.assert_rejected_at(record, parts)
            if field.get("type") == "array":
                for value in ([], [""], [None], [True], [{}], [[]]):
                    with self.subTest(field=parts, value=value):
                        record = copy.deepcopy(self.artifact)
                        self.parent(record, parts)[parts[-1]] = value
                        error_parts = parts if not value else parts + (0,)
                        self.assert_rejected_at(record, error_parts)

    def test_all_required_fields(self):
        objects = [((), self.schema)] + list(self.schema_fields(self.schema))
        for parts, field in objects:
            for required in field.get("required", []):
                with self.subTest(field=parts + (required,)):
                    record = copy.deepcopy(self.artifact)
                    obj = record
                    for name in parts:
                        obj = obj[name]
                    del obj[required]
                    self.assert_rejected_at(record, parts + (required,))

    def test_version_enum_and_commit_patterns(self):
        for name, value in (
            ("artifact_version", "2.0"),
            ("artifact_kind", "passed"),
            ("catalog_commit", "a" * 39),
            ("source_commit", "A" * 40),
        ):
            with self.subTest(field=name):
                record = copy.deepcopy(self.artifact)
                record[name] = value
                self.assert_rejected_at(record, (name,))

    def test_unavailable_schema_fails_closed(self):
        schema_path = self.base / "schema.json"
        for content in (None, "{broken", "[]", "null"):
            with self.subTest(content=content):
                if content is not None:
                    schema_path.write_text(content, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    result = self.validate()
                self.assertEqual(result["verdict"], "artifact_invalid", result)
                self.assertTrue(any("cannot load artifact schema" in e for e in result["errors"]))

    def test_paths_must_identify_files(self):
        for field in ("transcript", "artifact_paths", "screenshot_paths"):
            for value in ("directory", str(self.base / "directory"), "missing.txt", "bad\u0000path"):
                with self.subTest(field=field, value=value):
                    record = copy.deepcopy(self.artifact)
                    if field == "transcript":
                        record["execution"]["commands_or_transcript_path"] = value
                    elif field == "artifact_paths":
                        record["evidence"]["artifact_paths"] = [value]
                    else:
                        record["scenario_requirements"]["visual_or_browser"] = True
                        record["evidence"]["visual"] = {
                            "screenshot_paths": [value],
                            "website_url_or_mirror": "recorded mirror",
                            "viewport": {},
                        }
                    result = self.validate(record)
                    self.assertEqual(result["verdict"], "artifact_incomplete", result)
                    self.assertTrue(result["errors"])

    def test_absolute_and_repo_relative_file_paths_remain_accepted(self):
        with patch.object(validator, "ROOT", self.base):
            nested = self.base / "nested"
            nested.mkdir()
            self.path = nested / "artifact.json"
            self.artifact["evidence"]["artifact_paths"] = [str(self.base / "result.json"), "transcript.txt"]
            self.path.write_text(json.dumps(self.artifact), encoding="utf-8")
            result = validator.validate_artifact(
                self.path,
                ROOT / "data" / "skills_catalog.json",
                ROOT / "data" / "benchmark_scenarios.json",
            )
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_context_memory_boolean_numbers_are_incomplete(self):
        self.artifact["scenario_requirements"]["context_memory"] = True
        for before, after, delta in ((True, 1, None), (2, True, None), (1, 2, True), ("2", 1, None)):
            with self.subTest(before=before, after=after, delta=delta):
                self.artifact["evidence"]["context_memory"] = {
                    "delayed_recall_probes": ["recorded probe"],
                    "token_usage_before": before,
                    "token_usage_after": after,
                    "quality_delta": delta,
                }
                self.assertEqual(self.validate()["verdict"], "artifact_incomplete")

    def test_domain_rules_still_reject_incomplete_records(self):
        mutations = (
            ("benchmark_status", "passed"),
            ("skill_id", "unknown-skill"),
            ("scenario_id", "unknown-scenario"),
            ("source_repo", "incorrect/repo"),
            ("artifact_kind", "independent_benchmark"),
        )
        for name, value in mutations:
            with self.subTest(field=name):
                record = copy.deepcopy(self.artifact)
                record[name] = value
                self.assertEqual(self.validate(record)["verdict"], "artifact_incomplete")

    def test_cli_returns_json_for_malformed_fields(self):
        self.artifact["input_snapshot"] = None
        self.path.write_text(json.dumps(self.artifact), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"), str(self.path)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["verdict"], "artifact_invalid")
        self.assertEqual(completed.stderr, "")

    def test_unreadable_json_and_non_object_roots(self):
        for text in ("{broken", "null", "[]", '"text"', "true", "42"):
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                result = validator.validate_artifact(self.path)
                self.assertEqual(result["verdict"], "artifact_invalid", result)
                self.assertTrue(result["errors"])
        self.path.unlink()
        self.assertEqual(validator.validate_artifact(self.path)["verdict"], "artifact_invalid")

    def test_batch_cli_reports_invalid_and_incomplete_records_without_crashing(self):
        records = self.base / "records"
        for name in ("complete", "invalid", "incomplete"):
            directory = records / name
            directory.mkdir(parents=True)
            record = copy.deepcopy(self.artifact)
            record["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
            record["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
            if name == "invalid":
                record["skill_id"] = []
            elif name == "incomplete":
                record["execution"]["commands_or_transcript_path"] = str(self.base / "directory")
            (directory / "artifact.json").write_text(json.dumps(record), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"),
             "--validate-all", str(records)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stderr)
        self.assertIn("artifact_invalid", completed.stderr)
        self.assertIn("artifact_incomplete", completed.stderr)
        self.assertNotIn(str(records / "complete"), completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)

    def test_additional_properties_policy_and_pointer_escaping(self):
        schema = {"type": "object", "properties": {"known": {"type": "string"}}}
        for policy, value, expected in (
            (True, [], []),
            (False, "extra", ["/a~1b~0c:"]),
            ({"type": "string"}, 1, ["/a~1b~0c:"]),
            ({"type": "string"}, "extra", []),
        ):
            with self.subTest(policy=policy, value=value):
                errors = []
                validator._schema_walk(
                    dict(schema, additionalProperties=policy),
                    {"known": "value", "a/b~c": value}, [], errors,
                )
                self.assertEqual([error.split(":")[0] + ":" for error in errors], expected)


if __name__ == "__main__":
    unittest.main()
