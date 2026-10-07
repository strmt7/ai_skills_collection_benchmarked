import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import check_benchmark_artifact as validator


class ArtifactValidationRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.artifact = copy.deepcopy(self.schema["examples"][0])
        self.path = self.base / "artifact.json"
        self.catalog = self.base / "catalog.json"
        self.scenarios = self.base / "scenarios.json"
        self.write_json(self.catalog, [{
            "id": self.artifact["skill_id"],
            "commit_sha": self.artifact["source_commit"],
            "source_repo": self.artifact["source_repo"],
            "source_path": self.artifact["source_path"],
            "benchmark_scenarios": [self.artifact["scenario_id"]],
        }])
        self.write_json(self.scenarios, [{
            "id": self.artifact["scenario_id"],
            "dataset_track_id": "source-skill-repository",
        }])
        (self.base / "transcript.txt").write_text("Recorded commands\n", encoding="utf-8")
        (self.base / "result.json").write_text("{}", encoding="utf-8")

    def write_json(self, path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=None):
        self.write_json(self.path, self.artifact if artifact is None else artifact)
        return validator.validate_artifact(self.path, self.catalog, self.scenarios)

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], {"artifact_invalid", "artifact_incomplete"})
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(any(pointer in error for error in result["errors"]), result)

    def test_complete_provenance_keeps_warning(self):
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete")
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("do not count" in warning for warning in result["warnings"]))

    def test_complete_independent_record_with_visual_and_memory_evidence(self):
        self.artifact["artifact_kind"] = "independent_benchmark"
        self.write_json(self.scenarios, [{"id": self.artifact["scenario_id"], "dataset_track_id": "external"}])
        self.artifact["independence"].update({
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
        })
        self.artifact["scenario_requirements"] = {
            "visual_or_browser": True, "context_memory": True, "token_efficiency_claim": True,
        }
        self.artifact["evidence"].update({
            "visual": {
                "screenshot_paths": ["result.json"],
                "website_url_or_mirror": "https://example.invalid/",
                "viewport": {"width": 1280, "height": 720},
            },
            "context_memory": {
                "delayed_recall_probes": ["remember fixture identifier"],
                "token_usage_before": 100, "token_usage_after": 80,
            },
        })
        self.assertEqual(self.validate(), {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_permitted_metadata_and_descriptive_metrics_are_accepted(self):
        self.artifact["extra_metadata"] = {"tags": [None, True, 3]}
        for value in list(self.artifact.values()):
            if isinstance(value, dict):
                value["extra_metadata"] = {"arbitrary": [None, "value"]}
        self.artifact["metrics"]["verdict"] = "passed"
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_schema_additional_properties_false_is_enforced(self):
        schema = copy.deepcopy(self.schema)
        schema["properties"]["runner"]["additionalProperties"] = False
        schema_path = self.base / "schema.json"
        self.write_json(schema_path, schema)
        self.artifact["runner"]["unexpected/~field"] = "metadata"
        with patch.object(validator, "SCHEMA_PATH", schema_path):
            result = self.validate()
        self.assertEqual(result["verdict"], "artifact_invalid")
        self.assert_rejected(result, "/runner/unexpected~1~0field")

    def test_domain_failures_remain_incomplete(self):
        cases = [
            ("execution", "fresh_session", False),
            ("input_snapshot", "is_real", False),
            ("execution", "commands_or_transcript_path", "missing.txt"),
            ("evidence", "artifact_paths", ["missing.txt"]),
            (None, "benchmark_status", "passed"),
            (None, "verdict", "passed"),
        ]
        for parent, field, value in cases:
            with self.subTest(parent=parent, field=field):
                artifact = copy.deepcopy(self.artifact)
                (artifact if parent is None else artifact[parent])[field] = value
                result = self.validate(artifact)
                self.assertEqual(result["verdict"], "artifact_incomplete")
                self.assert_rejected(result)

    def test_complete_record_matches_bundled_catalog_and_scenarios(self):
        catalog = validator.load_json(validator.ROOT / "data" / "skills_catalog.json")
        scenarios = validator.load_json(validator.ROOT / "data" / "benchmark_scenarios.json")
        skill = catalog[0]
        scenario = next(scenario for scenario in scenarios if
                        scenario["id"] in skill["benchmark_scenarios"] and
                        scenario.get("dataset_track_id") == "source-skill-repository")
        self.artifact.update({
            "skill_id": skill["id"], "scenario_id": scenario["id"],
            "source_commit": skill["commit_sha"], "source_repo": skill["source_repo"],
            "source_path": skill["source_path"],
        })
        self.write_json(self.path, self.artifact)
        result = validator.validate_artifact(self.path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_malformed_top_level_fields_never_crash(self):
        for field in self.schema["required"]:
            for value in (None, [], {}, 42, True):
                if field in {"runner", "scenario_requirements", "input_snapshot", "execution", "outputs", "metrics", "independence", "evidence"} and value == {}:
                    continue
                with self.subTest(field=field, value=value):
                    artifact = copy.deepcopy(self.artifact)
                    artifact[field] = value
                    self.assert_rejected(self.validate(artifact), "/" + field)

    def test_nested_schema_types_are_enforced(self):
        cases = [
            ("runner", "timestamp_utc", 123), ("runner", "tool", []),
            ("runner", "model_or_runtime", {}), ("runner", "batch_name", False),
            ("input_snapshot", "kind", True), ("input_snapshot", "identifier", []),
            ("input_snapshot", "is_real", 1), ("execution", "fresh_session", 1),
            ("execution", "commands_or_transcript_path", {}),
            ("scenario_requirements", "context_memory", 1),
            ("scenario_requirements", "visual_or_browser", "true"),
            ("scenario_requirements", "token_efficiency_claim", []),
            ("independence", "task_defined_outside_skill", 1),
            ("independence", "evaluator_defined_outside_skill", "true"),
            ("independence", "expected_result_defined_outside_skill", None),
            ("independence", "uses_exact_skill_content_for_expected_result", {}),
            ("independence", "skill_content_usage", []),
            ("evidence", "visual", []), ("evidence", "context_memory", False),
            ("evidence", "artifact_paths", [None]), ("evidence", "citations_or_paths", [{}]),
        ]
        for parent, field, value in cases:
            with self.subTest(parent=parent, field=field):
                artifact = copy.deepcopy(self.artifact)
                artifact[parent][field] = value
                self.assert_rejected(self.validate(artifact), f"/{parent}/{field}")

    def test_empty_strings_missing_fields_patterns_and_arrays(self):
        cases = [
            (["input_snapshot", "kind"], ""),
            (["runner", "timestamp_utc"], ""),
            (["runner", "tool"], ""), (["runner", "model_or_runtime"], ""),
            (["input_snapshot", "identifier"], ""),
            (["independence", "skill_content_usage"], ""),
            (["execution", "commands_or_transcript_path"], ""),
            (["skill_id"], ""), (["scenario_id"], ""),
            (["source_repo"], ""), (["source_path"], ""),
            (["artifact_version"], "2.0"), (["artifact_kind"], "recorded"),
            (["catalog_commit"], "a" * 39), (["source_commit"], "A" * 40),
            (["evidence", "artifact_paths"], []),
            (["evidence", "citations_or_paths"], []), (["objective_checks"], []),
            (["evidence", "artifact_paths", 0], ""),
            (["evidence", "citations_or_paths", 0], ""), (["objective_checks", 0], ""),
        ]
        for path, value in cases:
            with self.subTest(path=path, value=value):
                artifact = copy.deepcopy(self.artifact)
                parent = artifact
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = value
                self.assert_rejected(self.validate(artifact), "/" + "/".join(map(str, path)))
        for parent, fields in [(None, self.schema["required"])] + [
            (key, schema["required"]) for key, schema in self.schema["properties"].items() if "required" in schema
        ]:
            for field in fields:
                with self.subTest(parent=parent, missing=field):
                    artifact = copy.deepcopy(self.artifact)
                    del (artifact if parent is None else artifact[parent])[field]
                    self.assert_rejected(self.validate(artifact), f"/{parent}/{field}" if parent else "/" + field)

    def test_schema_unavailable_rejects_otherwise_complete_record(self):
        schema_path = self.base / "schema.json"
        for contents in (None, "{broken", "[]", "null"):
            with self.subTest(contents=contents):
                if contents is not None:
                    schema_path.write_text(contents, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    self.assert_rejected(self.validate(), "schema")

    def test_transcript_evidence_and_screenshot_paths_must_be_files(self):
        directory = self.base / "directory"
        directory.mkdir()
        for bad_path in ("directory", str(directory), "missing.txt", "bad\0path"):
            for target in ("transcript", "evidence", "screenshot"):
                with self.subTest(target=target, path=bad_path):
                    artifact = copy.deepcopy(self.artifact)
                    if target == "transcript":
                        artifact["execution"]["commands_or_transcript_path"] = bad_path
                    elif target == "evidence":
                        artifact["evidence"]["artifact_paths"] = [bad_path]
                    else:
                        artifact["scenario_requirements"]["visual_or_browser"] = True
                        artifact["evidence"]["visual"] = {
                            "screenshot_paths": [bad_path],
                            "website_url_or_mirror": "https://example.invalid/",
                            "viewport": {},
                        }
                    self.assert_rejected(self.validate(artifact))

    def test_absolute_and_repo_relative_file_paths_are_accepted(self):
        self.artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        self.artifact["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")
        self.artifact["evidence"]["artifact_paths"] = ["evaluators/benchmark_run_artifact.schema.json"]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_invalid_json_and_root_are_structured(self):
        for contents in ("{broken", "[]", "null"):
            with self.subTest(contents=contents):
                self.path.write_text(contents, encoding="utf-8")
                result = validator.validate_artifact(self.path, self.catalog, self.scenarios)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assert_rejected(result)

    def test_single_and_batch_cli_report_malformed_record(self):
        self.artifact["skill_id"] = []
        self.validate()
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = validator.main([str(self.path), "--catalog", str(self.catalog), "--scenarios", str(self.scenarios)])
        self.assertIn(code, (1, 2))
        self.assert_rejected(json.loads(output.getvalue()), "/skill_id")
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            code = validator.main(["--validate-all", str(self.base), "--catalog", str(self.catalog), "--scenarios", str(self.scenarios)])
        self.assertEqual(code, 2)
        self.assertIn("/skill_id", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
