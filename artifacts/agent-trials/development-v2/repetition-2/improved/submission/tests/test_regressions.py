"""Behavioral regressions for benchmark artifact validation (stdlib only)."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import check_benchmark_artifact as validator


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="artifact-test-", dir=ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.artifact_path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        self.schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.artifact = copy.deepcopy(self.schema["examples"][0])
        self.artifact.update(skill_id="test-skill", scenario_id="provenance-scenario")
        self.write_json(self.catalog_path, [{
            "id": "test-skill",
            "commit_sha": self.artifact["source_commit"],
            "source_repo": self.artifact["source_repo"],
            "source_path": self.artifact["source_path"],
            "benchmark_scenarios": ["provenance-scenario", "independent-scenario"],
        }])
        self.write_json(self.scenarios_path, [
            {"id": "provenance-scenario", "dataset_track_id": "source-skill-repository"},
            {"id": "independent-scenario", "dataset_track_id": "external-fixture"},
        ])
        (self.base / "transcript.txt").write_text("Recorded commands and results\n", encoding="utf-8")
        self.write_json(self.base / "result.json", {"recorded": True})
        (self.base / "screenshot.png").write_bytes(b"recorded visual evidence")
        (self.base / "directory").mkdir()

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, artifact=...):
        self.write_json(self.artifact_path, self.artifact if artifact is ... else artifact)
        return validator.validate_artifact(self.artifact_path, self.catalog_path, self.scenarios_path)

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], {"artifact_invalid", "artifact_incomplete"})
        self.assertTrue(result["errors"])
        self.assertTrue(all(isinstance(message, str) for message in result["errors"]))
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(any(pointer in message for message in result["errors"]), result)

    def make_independent(self):
        self.artifact.update(artifact_kind="independent_benchmark", scenario_id="independent-scenario")
        self.artifact["independence"].update(
            task_defined_outside_skill=True,
            evaluator_defined_outside_skill=True,
            expected_result_defined_outside_skill=True,
            uses_exact_skill_content_for_expected_result=False,
        )

    def add_visual_and_memory(self):
        self.artifact["scenario_requirements"].update(
            visual_or_browser=True, context_memory=True, token_efficiency_claim=True,
        )
        self.artifact["evidence"].update(
            visual={
                "screenshot_paths": ["screenshot.png"],
                "website_url_or_mirror": "https://example.invalid/recorded-page",
                "viewport": {"width": 1280, "height": 720},
            },
            context_memory={
                "delayed_recall_probes": [{"question": "fixture identifier", "correct": True}],
                "token_usage_before": 100,
                "token_usage_after": 80,
                "quality_delta": 0,
            },
        )

    def test_complete_provenance_with_permitted_extra_metadata(self):
        self.artifact["batch_metadata"] = {"notes": ["retained", {"nested": True}]}
        for name in ("runner", "input_snapshot", "execution", "independence",
                     "scenario_requirements", "evidence", "outputs", "metrics"):
            self.artifact[name]["extra_metadata"] = {"revision": 2}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("provenance_check" in warning for warning in result["warnings"]))

    def test_complete_independent_record_with_visual_and_memory_evidence(self):
        self.make_independent()
        self.add_visual_and_memory()
        result = self.validate()
        self.assertEqual(result, {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_complete_record_matches_bundled_catalog_and_scenario(self):
        skill = json.loads((ROOT / "data" / "skills_catalog.json").read_text(encoding="utf-8"))[0]
        self.artifact.update(
            skill_id=skill["id"], scenario_id=skill["benchmark_scenarios"][0],
            source_commit=skill["commit_sha"], source_repo=skill["source_repo"],
            source_path=skill["source_path"],
        )
        self.write_json(self.artifact_path, self.artifact)
        result = validator.validate_artifact(self.artifact_path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_malformed_top_level_fields_return_structured_verdicts(self):
        replacements = (None, [], {}, 17, True, "wrong-type")
        for name, schema in self.schema["properties"].items():
            expected = {"string": str, "object": dict, "array": list}[schema["type"]]
            for value in replacements:
                if isinstance(value, expected):
                    continue
                with self.subTest(field=name, value=value):
                    record = copy.deepcopy(self.artifact)
                    record[name] = value
                    self.assert_rejected(self.validate(record), f"/{name}")

    def test_malformed_nested_fields_return_structured_verdicts(self):
        for parent, schema in self.schema["properties"].items():
            for name, child in schema.get("properties", {}).items():
                invalid = {"string": [], "boolean": "true", "array": {}, "object": []}[child["type"]]
                with self.subTest(parent=parent, field=name):
                    record = copy.deepcopy(self.artifact)
                    record[parent][name] = invalid
                    self.assert_rejected(self.validate(record), f"/{parent}/{name}")

    def test_missing_required_fields_at_every_declared_object(self):
        for name in self.schema["required"]:
            with self.subTest(field=name):
                record = copy.deepcopy(self.artifact)
                del record[name]
                self.assert_rejected(self.validate(record), f"/{name}")
        for parent, schema in self.schema["properties"].items():
            for name in schema.get("required", []):
                with self.subTest(parent=parent, field=name):
                    record = copy.deepcopy(self.artifact)
                    del record[parent][name]
                    self.assert_rejected(self.validate(record), f"/{parent}/{name}")

    def test_every_declared_min_length_is_enforced(self):
        def visit(schema, value, path):
            if "minLength" in schema:
                yield path
            for name, child in schema.get("properties", {}).items():
                if name in value:
                    yield from visit(child, value[name], path + [name])
            if isinstance(value, list) and "items" in schema:
                for index, item in enumerate(value):
                    yield from visit(schema["items"], item, path + [index])

        for path in visit(self.schema, self.artifact, []):
            with self.subTest(path=path):
                record = copy.deepcopy(self.artifact)
                parent = record
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = ""
                self.assert_rejected(self.validate(record), "/" + "/".join(map(str, path)))

    def test_pattern_enum_and_array_constraints(self):
        mutations = [
            (["artifact_version"], "2.0"),
            (["artifact_kind"], "unrecognized"),
            (["catalog_commit"], "A" * 40),
            (["source_commit"], "short"),
            (["objective_checks"], []),
            (["objective_checks"], [{}]),
            (["evidence", "artifact_paths"], []),
            (["evidence", "artifact_paths"], [True]),
            (["evidence", "citations_or_paths"], []),
            (["evidence", "citations_or_paths"], [None]),
        ]
        for path, value in mutations:
            with self.subTest(path=path, value=value):
                record = copy.deepcopy(self.artifact)
                parent = record
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = value
                self.assert_rejected(self.validate(record), "/" + "/".join(path))

    def test_additional_properties_false_and_schema_are_enforced(self):
        schema_path = self.base / "schema.json"
        for additional, value, accepted in ((False, "metadata", False),
                                             ({"type": "string", "minLength": 1}, [], False),
                                             ({"type": "string", "minLength": 1}, "metadata", True)):
            with self.subTest(additional=additional, value=value):
                schema = copy.deepcopy(self.schema)
                schema["properties"]["runner"]["additionalProperties"] = additional
                self.write_json(schema_path, schema)
                self.artifact["runner"]["extra/~key"] = value
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    result = self.validate()
                if accepted:
                    self.assertEqual(result["verdict"], "artifact_complete", result)
                else:
                    self.assert_rejected(result, "/runner/extra~1~0key")

    def test_unavailable_or_unreadable_schema_rejects_complete_record(self):
        schema_path = self.base / "unavailable-schema.json"
        for contents in (None, "{broken JSON", "[]", "null"):
            with self.subTest(contents=contents):
                if contents is not None:
                    schema_path.write_text(contents, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    self.assert_rejected(self.validate(), "schema")
        with patch.object(validator, "SCHEMA_PATH", self.base / "directory"):
            self.assert_rejected(self.validate(), "schema")

    def test_transcript_and_evidence_must_be_files(self):
        for path in ("directory", "missing.txt", "bad\x00path"):
            for field in ("transcript", "artifact_paths", "screenshot_paths"):
                with self.subTest(path=path, field=field):
                    record = copy.deepcopy(self.artifact)
                    if field == "transcript":
                        record["execution"]["commands_or_transcript_path"] = path
                    elif field == "artifact_paths":
                        record["evidence"][field] = [path]
                    else:
                        record["scenario_requirements"]["visual_or_browser"] = True
                        record["evidence"]["visual"] = {
                            field: [path], "website_url_or_mirror": "recorded mirror", "viewport": {},
                        }
                    self.assert_rejected(self.validate(record))

    def test_local_repo_relative_and_absolute_file_paths_remain_accepted(self):
        for path in (self.base / "transcript.txt", (self.base / "transcript.txt").relative_to(ROOT)):
            with self.subTest(path=path):
                record = copy.deepcopy(self.artifact)
                record["execution"]["commands_or_transcript_path"] = str(path)
                record["evidence"]["artifact_paths"] = [str(path)]
                result = self.validate(record)
                self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_domain_invariants_still_reject_incomplete_records(self):
        mutations = [
            (["benchmark_status"], "passed"), (["verdict"], "passed"),
            (["skill_id"], "unknown"), (["scenario_id"], "unknown"),
            (["source_repo"], "different/repo"), (["source_commit"], "1" * 40),
            (["execution", "fresh_session"], False), (["input_snapshot", "is_real"], False),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                record = copy.deepcopy(self.artifact)
                parent = record
                for part in path[:-1]:
                    parent = parent[part]
                parent[path[-1]] = value
                self.assert_rejected(self.validate(record))
        self.make_independent()
        self.artifact["independence"]["task_defined_outside_skill"] = False
        self.assert_rejected(self.validate(), "task_defined_outside_skill")

    def test_malformed_unconstrained_visual_and_memory_payloads(self):
        self.add_visual_and_memory()
        mutations = [
            (["visual", "screenshot_paths"], [{}]),
            (["visual", "viewport"], []),
            (["context_memory", "delayed_recall_probes"], {}),
            (["context_memory", "token_usage_before"], []),
            (["context_memory", "token_usage_after"], "80"),
        ]
        for path, value in mutations:
            with self.subTest(path=path):
                record = copy.deepcopy(self.artifact)
                record["evidence"][path[0]][path[1]] = value
                self.assert_rejected(self.validate(record))

    def test_unreadable_invalid_json_and_non_object_roots(self):
        self.assert_rejected(validator.validate_artifact(self.artifact_path), "cannot read artifact JSON")
        self.artifact_path.write_text("{broken JSON", encoding="utf-8")
        self.assert_rejected(validator.validate_artifact(self.artifact_path), "cannot read artifact JSON")
        for root in ([], None, 7, "artifact"):
            with self.subTest(root=root):
                self.assert_rejected(self.validate(root), "root must be an object")

    def test_cli_reports_malformed_record_as_json_and_batch_failure(self):
        self.artifact["skill_id"] = []
        self.write_json(self.artifact_path, self.artifact)
        args = ["--catalog", str(self.catalog_path), "--scenarios", str(self.scenarios_path)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = validator.main([str(self.artifact_path), *args])
        self.assertIn(code, (1, 2))
        self.assert_rejected(json.loads(stdout.getvalue()), "/skill_id")
        with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
            batch_code = validator.main(["--validate-all", str(self.base), *args])
        self.assertEqual(batch_code, 2)
        self.assertIn("/skill_id", stderr.getvalue())

    def test_cli_exit_codes_for_complete_invalid_and_incomplete_records(self):
        args = [str(self.artifact_path), "--catalog", str(self.catalog_path),
                "--scenarios", str(self.scenarios_path)]
        cases = [
            (self.artifact, "artifact_complete", 0),
            ([], "artifact_invalid", 1),
            ({**self.artifact, "execution": {
                "fresh_session": True, "commands_or_transcript_path": "missing.txt",
            }}, "artifact_incomplete", 2),
        ]
        for record, verdict, expected_code in cases:
            with self.subTest(verdict=verdict):
                self.write_json(self.artifact_path, record)
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = validator.main(args)
                self.assertEqual(code, expected_code)
                self.assertEqual(json.loads(stdout.getvalue())["verdict"], verdict)

    def test_filesystem_errors_become_incomplete_verdicts(self):
        for error in (OSError("unreadable path"), ValueError("unusable path")):
            with self.subTest(error=type(error).__name__):
                with patch.object(validator, "resolve_artifact_path", side_effect=error):
                    result = self.validate()
                self.assertEqual(result["verdict"], "artifact_incomplete", result)
                self.assertTrue(any("transcript" in message for message in result["errors"]))
                self.assertTrue(any("evidence" in message for message in result["errors"]))


if __name__ == "__main__":
    unittest.main()
