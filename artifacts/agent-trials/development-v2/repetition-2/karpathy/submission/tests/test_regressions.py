"""Regression coverage for benchmark artifact validation and CLI verdicts."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tools import check_benchmark_artifact as validator


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=validator.ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.artifact = copy.deepcopy(schema["examples"][0])
        self.path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        self.catalog = [{
            "id": self.artifact["skill_id"],
            "commit_sha": self.artifact["source_commit"],
            "source_repo": self.artifact["source_repo"],
            "source_path": self.artifact["source_path"],
            "benchmark_scenarios": [self.artifact["scenario_id"], "runtime-scenario"],
        }]
        self.scenarios = [
            {"id": self.artifact["scenario_id"], "dataset_track_id": "source-skill-repository"},
            {"id": "runtime-scenario", "dataset_track_id": "external-fixture"},
        ]
        self.write_json(self.catalog_path, self.catalog)
        self.write_json(self.scenarios_path, self.scenarios)
        (self.base / "transcript.txt").write_text("recorded commands\n", encoding="utf-8")
        self.write_json(self.base / "result.json", {"result": "recorded"})

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=None):
        self.write_json(self.path, self.artifact if artifact is None else artifact)
        return validator.validate_artifact(self.path, self.catalog_path, self.scenarios_path)

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], ("artifact_invalid", "artifact_incomplete"))
        self.assertIsInstance(result["errors"], list)
        self.assertTrue(result["errors"])
        self.assertTrue(all(isinstance(error, str) for error in result["errors"]))
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(any(pointer in error for error in result["errors"]), result)

    def test_complete_provenance_and_permitted_metadata(self):
        self.artifact["extra_metadata"] = {"tags": ["recorded"], "optional": None}
        for field in ("runner", "scenario_requirements", "input_snapshot", "execution",
                      "outputs", "metrics", "independence", "evidence"):
            self.artifact[field]["extra_metadata"] = {"arbitrary": [1, True, None]}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("provenance_check" in warning for warning in result["warnings"]))

    def test_complete_independent_visual_and_memory_record(self):
        self.artifact["artifact_kind"] = "independent_benchmark"
        self.artifact["scenario_id"] = "runtime-scenario"
        self.artifact["independence"].update({
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
        })
        self.artifact["scenario_requirements"].update({
            "visual_or_browser": True, "context_memory": True, "token_efficiency_claim": True,
        })
        (self.base / "screenshot.png").write_bytes(b"recorded screenshot fixture")
        self.artifact["evidence"]["visual"] = {
            "screenshot_paths": ["screenshot.png"],
            "website_url_or_mirror": "https://example.invalid",
            "viewport": {"width": 1280, "height": 720},
        }
        self.artifact["evidence"]["context_memory"] = {
            "delayed_recall_probes": [{"answer": "correct"}],
            "token_usage_before": 100, "token_usage_after": 50,
        }
        self.assertEqual(self.validate(), {
            "verdict": "artifact_complete", "errors": [], "warnings": [],
        })

    def test_complete_record_with_bundled_catalog_and_scenarios(self):
        skill = validator.load_json(validator.ROOT / "data" / "skills_catalog.json")[0]
        self.artifact.update({
            "skill_id": skill["id"], "scenario_id": skill["benchmark_scenarios"][0],
            "source_commit": skill["commit_sha"], "source_repo": skill["source_repo"],
            "source_path": skill["source_path"],
        })
        self.write_json(self.path, self.artifact)
        result = validator.validate_artifact(self.path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_non_object_input_snapshot_returns_structured_verdict(self):
        for value in (None, [], "snapshot", 42, True):
            with self.subTest(value=value):
                artifact = copy.deepcopy(self.artifact)
                artifact["input_snapshot"] = value
                self.assert_rejected(self.validate(artifact), "/input_snapshot")

    def test_malformed_top_level_fields_do_not_crash(self):
        for field, value in (
            ("artifact_kind", []), ("artifact_kind", {}),
            ("skill_id", []), ("skill_id", {}),
            ("scenario_id", []), ("scenario_id", {}),
            ("runner", None), ("execution", []), ("scenario_requirements", True),
            ("independence", "invalid"), ("evidence", 5),
            ("outputs", []), ("metrics", False), ("objective_checks", {}),
            ("catalog_commit", 123), ("source_commit", None),
        ):
            with self.subTest(field=field, value=value):
                artifact = copy.deepcopy(self.artifact)
                artifact[field] = value
                self.assert_rejected(self.validate(artifact), "/" + field)

    def test_malformed_nested_fields_and_array_items(self):
        for parts, value in (
            (("runner", "timestamp_utc"), True),
            (("runner", "tool"), {}),
            (("runner", "batch_name"), 3),
            (("input_snapshot", "identifier"), []),
            (("input_snapshot", "is_real"), 1),
            (("execution", "fresh_session"), 1),
            (("execution", "commands_or_transcript_path"), {}),
            (("scenario_requirements", "visual_or_browser"), "true"),
            (("independence", "task_defined_outside_skill"), 1),
            (("evidence", "artifact_paths", 0), {}),
            (("evidence", "citations_or_paths", 0), None),
            (("evidence", "visual"), []),
            (("evidence", "context_memory"), False),
            (("objective_checks", 0), 7),
        ):
            with self.subTest(parts=parts):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = value
                self.assert_rejected(self.validate(artifact), "/" + "/".join(map(str, parts)))

    def test_schema_min_length_is_enforced(self):
        for parts in (
            ("skill_id",), ("scenario_id",), ("source_repo",), ("source_path",),
            ("runner", "timestamp_utc"), ("runner", "tool"), ("runner", "model_or_runtime"),
            ("input_snapshot", "kind"), ("input_snapshot", "identifier"),
            ("execution", "commands_or_transcript_path"),
            ("independence", "skill_content_usage"),
            ("evidence", "artifact_paths", 0), ("evidence", "citations_or_paths", 0),
            ("objective_checks", 0),
        ):
            with self.subTest(parts=parts):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                target[parts[-1]] = ""
                self.assert_rejected(self.validate(artifact), "/" + "/".join(map(str, parts)))

    def test_required_fields_patterns_enums_and_min_items(self):
        for parts in (("outputs",), ("runner", "tool"), ("input_snapshot", "kind"),
                      ("evidence", "citations_or_paths")):
            with self.subTest(missing=parts):
                artifact = copy.deepcopy(self.artifact)
                target = artifact
                for part in parts[:-1]:
                    target = target[part]
                del target[parts[-1]]
                self.assert_rejected(self.validate(artifact), "/" + "/".join(parts))
        for field, value in (("artifact_version", "2.0"), ("artifact_kind", "passed"),
                             ("catalog_commit", "A" * 40), ("source_commit", "a" * 39),
                             ("objective_checks", [])):
            with self.subTest(field=field):
                artifact = copy.deepcopy(self.artifact)
                artifact[field] = value
                self.assert_rejected(self.validate(artifact), "/" + field)
        for field in ("artifact_paths", "citations_or_paths"):
            with self.subTest(empty_array=field):
                artifact = copy.deepcopy(self.artifact)
                artifact["evidence"][field] = []
                self.assert_rejected(self.validate(artifact), "/evidence/" + field)

    def test_schema_unavailable_or_unreadable_fails_closed(self):
        schema_path = self.base / "schema.json"
        for contents in (None, "{", "[]", "null"):
            with self.subTest(contents=contents):
                if contents is not None:
                    schema_path.write_text(contents, encoding="utf-8")
                with mock.patch.object(validator, "SCHEMA_PATH", schema_path):
                    result = self.validate()
                self.assert_rejected(result)
                self.assertTrue(any("schema" in error.lower() for error in result["errors"]), result)

    def test_additional_properties_follow_schema_policy(self):
        schema = validator.load_json(validator.SCHEMA_PATH)
        self.artifact["runner"]["extra_metadata"] = {"recorded": True}
        schema["properties"]["runner"]["additionalProperties"] = False
        with mock.patch.object(validator, "_load_schema", return_value=schema):
            self.assert_rejected(self.validate(), "/runner/extra_metadata")

        schema["properties"]["runner"]["additionalProperties"] = {"type": "string"}
        with mock.patch.object(validator, "_load_schema", return_value=schema):
            self.assert_rejected(self.validate(), "/runner/extra_metadata")
            self.artifact["runner"]["extra_metadata"] = "recorded"
            self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_transcript_and_evidence_paths_must_be_files(self):
        (self.base / "directory").mkdir()
        for field in ("transcript", "evidence", "screenshot"):
            for path in ("directory", "missing.txt", "bad\x00path"):
                with self.subTest(field=field, path=path):
                    artifact = copy.deepcopy(self.artifact)
                    if field == "transcript":
                        artifact["execution"]["commands_or_transcript_path"] = path
                    elif field == "evidence":
                        artifact["evidence"]["artifact_paths"] = [path]
                    else:
                        artifact["scenario_requirements"]["visual_or_browser"] = True
                        artifact["evidence"]["visual"] = {
                            "screenshot_paths": [path],
                            "website_url_or_mirror": "https://example.invalid",
                            "viewport": {},
                        }
                    self.assert_rejected(self.validate(artifact))

    def test_absolute_and_repo_relative_files_are_accepted(self):
        self.artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        self.artifact["evidence"]["artifact_paths"] = [
            str(self.base / "result.json"), "data/benchmark_scenarios.json",
        ]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_domain_errors_remain_incomplete(self):
        for field in ("benchmark_status", "verdict"):
            with self.subTest(field=field):
                artifact = copy.deepcopy(self.artifact)
                artifact[field] = "passed"
                self.assertEqual(self.validate(artifact)["verdict"], "artifact_incomplete")
        self.artifact["execution"]["fresh_session"] = False
        self.assertEqual(self.validate()["verdict"], "artifact_incomplete")

    def test_invalid_json_and_non_object_roots(self):
        for contents in ("{", "null", "[]", "true", '"artifact"'):
            with self.subTest(contents=contents):
                self.path.write_text(contents, encoding="utf-8")
                result = validator.validate_artifact(self.path, self.catalog_path, self.scenarios_path)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assert_rejected(result)

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(validator.ROOT / "tools" / "check_benchmark_artifact.py"),
             *map(str, args), "--catalog", str(self.catalog_path),
             "--scenarios", str(self.scenarios_path)],
            cwd=validator.ROOT, capture_output=True, text=True, check=False,
        )

    def test_cli_structured_verdicts_and_exit_codes(self):
        for mode in ("complete", "malformed", "missing_file"):
            with self.subTest(mode=mode):
                artifact = copy.deepcopy(self.artifact)
                if mode == "malformed":
                    artifact["input_snapshot"] = None
                elif mode == "missing_file":
                    artifact["execution"]["commands_or_transcript_path"] = "missing.txt"
                self.write_json(self.path, artifact)
                process = self.run_cli(self.path)
                result = json.loads(process.stdout)
                expected_code = {"artifact_complete": 0, "artifact_invalid": 1,
                                 "artifact_incomplete": 2}[result["verdict"]]
                self.assertEqual(process.returncode, expected_code, process.stderr)
                self.assertEqual(process.stderr, "")
                if mode == "complete":
                    self.assertEqual(result["verdict"], "artifact_complete")
                else:
                    self.assert_rejected(result)

    def test_validate_all_reports_malformed_artifact_without_traceback(self):
        self.artifact["skill_id"] = []
        self.write_json(self.path, self.artifact)
        process = self.run_cli("--validate-all", self.base)
        self.assertEqual(process.returncode, 2, process.stderr)
        self.assertNotIn("Traceback", process.stderr)
        self.assertIn("/skill_id", process.stderr)


if __name__ == "__main__":
    unittest.main()
