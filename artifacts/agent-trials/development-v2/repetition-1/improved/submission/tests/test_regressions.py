"""Behavioral regressions for benchmark artifact validation (no network needed)."""

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import check_benchmark_artifact as validator


class ArtifactValidationTests(unittest.TestCase):
    def setUp(self):
        # Keep fixtures and all generated evidence inside the task workspace.
        self.temp = tempfile.TemporaryDirectory(dir=validator.ROOT / "tests")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.path = self.base / "artifact.json"
        self.catalog = self.base / "catalog.json"
        self.scenarios = self.base / "scenarios.json"
        self.catalog.write_text(json.dumps([{
            "id": "test-skill", "commit_sha": "a" * 40,
            "source_repo": "example/skills", "source_path": "SKILL.md",
            "benchmark_scenarios": ["source-proof", "runtime-check"],
        }]), encoding="utf-8")
        self.scenarios.write_text(json.dumps([
            {"id": "source-proof", "dataset_track_id": "source-skill-repository"},
            {"id": "runtime-check", "dataset_track_id": "external-fixture"},
        ]), encoding="utf-8")
        for name in ("transcript.txt", "result.json", "screenshot.png"):
            (self.base / name).write_text("recorded evidence", encoding="utf-8")
        (self.base / "directory").mkdir()
        self.artifact = {
            "artifact_version": "1.0", "artifact_kind": "provenance_check",
            "skill_id": "test-skill", "scenario_id": "source-proof",
            "catalog_commit": "b" * 40, "source_commit": "a" * 40,
            "source_repo": "example/skills", "source_path": "SKILL.md",
            "runner": {"timestamp_utc": "2026-10-02T12:00:00Z",
                       "tool": "fixture-runner", "model_or_runtime": "python"},
            "scenario_requirements": {},
            "input_snapshot": {"kind": "source", "identifier": "pinned fixture", "is_real": True},
            "execution": {"fresh_session": True, "commands_or_transcript_path": "transcript.txt"},
            "outputs": {"result": "result.json"}, "metrics": {"count": 1},
            "independence": {"skill_content_usage": "provenance only"},
            "evidence": {"artifact_paths": ["result.json"], "citations_or_paths": ["SKILL.md"]},
            "objective_checks": ["source matches pinned commit"],
        }

    def validate(self, artifact=None):
        self.path.write_text(json.dumps(self.artifact if artifact is None else artifact), encoding="utf-8")
        return validator.validate_artifact(self.path, self.catalog, self.scenarios)

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], ("artifact_invalid", "artifact_incomplete"))
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(any(pointer in error for error in result["errors"]), result)

    def test_complete_provenance_and_extra_metadata_are_accepted(self):
        self.artifact["extra_metadata"] = {"revision": 3, "nullable": None}
        self.artifact["runner"]["batch_name"] = ""
        self.artifact["runner"]["custom"] = [1, 2]
        self.artifact["outputs"]["details"] = {"anything": True}
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["warnings"])

    def test_complete_independent_visual_and_memory_record_is_accepted(self):
        self.artifact.update(artifact_kind="independent_benchmark", scenario_id="runtime-check")
        self.artifact["independence"].update(
            task_defined_outside_skill=True, evaluator_defined_outside_skill=True,
            expected_result_defined_outside_skill=True,
            uses_exact_skill_content_for_expected_result=False,
        )
        self.artifact["scenario_requirements"] = {
            "visual_or_browser": True, "context_memory": True, "token_efficiency_claim": True,
        }
        self.artifact["evidence"]["visual"] = {
            "screenshot_paths": ["screenshot.png"], "website_url_or_mirror": "local mirror",
            "viewport": {"width": 1280, "height": 720},
        }
        self.artifact["evidence"]["context_memory"] = {
            "delayed_recall_probes": [{"answer": "correct"}],
            "token_usage_before": 100, "token_usage_after": 80,
        }
        result = self.validate()
        self.assertEqual(result, {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_malformed_top_level_fields_return_structured_errors(self):
        for key in self.artifact:
            for value in (None, [], {}, 42, True, "wrong type"):
                if isinstance(value, type(self.artifact[key])):
                    continue
                with self.subTest(field=key, value=value):
                    record = copy.deepcopy(self.artifact)
                    record[key] = value
                    self.assert_rejected(self.validate(record), "/" + key)

    def test_nested_schema_types_required_and_min_length(self):
        schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        expected_types = {"object": dict, "array": list, "string": str, "boolean": bool}

        def exercise(node, original, path):
            for key, child in node.get("properties", {}).items():
                field_path = path + [key]
                if key in original and child.get("type") == "object":
                    exercise(child, original[key], field_path)
                values = [None, [], {}, 7, True]
                if child.get("minLength"):
                    values.append("")
                for value in values:
                    if type(value) is expected_types[child["type"]]:
                        if value != "":
                            continue
                    with self.subTest(path=field_path, value=value):
                        record = copy.deepcopy(self.artifact)
                        parent = record
                        for part in path:
                            parent = parent[part]
                        parent[key] = value
                        self.assert_rejected(self.validate(record), "/" + "/".join(field_path))
                if key in node.get("required", []):
                    with self.subTest(missing=field_path):
                        record = copy.deepcopy(self.artifact)
                        parent = record
                        for part in path:
                            parent = parent[part]
                        del parent[key]
                        self.assert_rejected(self.validate(record), "/" + "/".join(field_path))

        exercise(schema, self.artifact, [])

    def test_schema_patterns_enum_and_array_constraints(self):
        cases = [(["artifact_version"], "2.0"), (["artifact_kind"], "unsupported"),
                 (["catalog_commit"], "A" * 40), (["source_commit"], "a" * 39)]
        for field in (["objective_checks"], ["evidence", "artifact_paths"],
                      ["evidence", "citations_or_paths"]):
            cases.extend((field, value) for value in ([], [""], [None], [42], [{}]))
        for field, value in cases:
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.artifact)
                parent = record
                for key in field[:-1]:
                    parent = parent[key]
                parent[field[-1]] = value
                self.assert_rejected(self.validate(record), "/" + "/".join(field))

    def test_unavailable_or_unreadable_schema_rejects_valid_record(self):
        schema_path = self.base / "schema.json"
        with patch.object(validator, "SCHEMA_PATH", schema_path):
            self.assert_rejected(self.validate(), "schema")
            for contents in ("{", "null", "[]"):
                with self.subTest(contents=contents):
                    schema_path.write_text(contents, encoding="utf-8")
                    self.assert_rejected(self.validate(), "schema")
            schema_path.unlink()
            schema_path.mkdir()
            self.assert_rejected(self.validate(), "schema")

    def test_additional_properties_false_is_enforced_with_pointer_escaping(self):
        schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        schema["properties"]["runner"]["additionalProperties"] = False
        schema_path = self.base / "strict-schema.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        self.artifact["runner"]["unknown~/field"] = "extra"
        with patch.object(validator, "SCHEMA_PATH", schema_path):
            self.assert_rejected(self.validate(), "/runner/unknown~0~1field")

    def test_paths_must_be_files_and_bad_path_strings_do_not_crash(self):
        for value in ("directory", ".", "missing.txt", "bad\x00path"):
            for field in ("transcript", "evidence", "screenshot"):
                with self.subTest(value=value, field=field):
                    record = copy.deepcopy(self.artifact)
                    if field == "transcript":
                        record["execution"]["commands_or_transcript_path"] = value
                    elif field == "evidence":
                        record["evidence"]["artifact_paths"] = [value]
                    else:
                        record["scenario_requirements"]["visual_or_browser"] = True
                        record["evidence"]["visual"] = {
                            "screenshot_paths": [value], "website_url_or_mirror": "mirror", "viewport": {},
                        }
                    self.assert_rejected(self.validate(record))

    def test_absolute_and_repository_relative_files_are_accepted(self):
        self.artifact["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        self.artifact["evidence"]["artifact_paths"] = [
            (self.base / "result.json").relative_to(validator.ROOT).as_posix(),
        ]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_domain_failures_remain_incomplete(self):
        cases = [("skill_id", "unknown"), ("scenario_id", "unknown"),
                 ("benchmark_status", "passed"), ("source_repo", "other/repo")]
        for key, value in cases:
            with self.subTest(key=key):
                record = copy.deepcopy(self.artifact)
                record[key] = value
                self.assertEqual(self.validate(record)["verdict"], "artifact_incomplete")

    def test_malformed_optional_visual_fields_are_incomplete(self):
        self.artifact["scenario_requirements"]["visual_or_browser"] = True
        visual = {"screenshot_paths": ["screenshot.png"],
                  "website_url_or_mirror": "local mirror", "viewport": {}}
        cases = [("screenshot_paths", value) for value in (None, [], {}, [None], [42], [""])]
        cases.extend(("viewport", value) for value in (None, [], "1280x720", 42))
        cases.append(("website_url_or_mirror", ""))
        for field, value in cases:
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.artifact)
                record["evidence"]["visual"] = dict(visual, **{field: value})
                result = self.validate(record)
                self.assertEqual(result["verdict"], "artifact_incomplete", result)
                self.assertTrue(result["errors"])

    def test_malformed_memory_counts_and_probes_are_incomplete(self):
        self.artifact["scenario_requirements"]["context_memory"] = True
        memory = {"delayed_recall_probes": ["correct"],
                  "token_usage_before": 100, "token_usage_after": 80}
        cases = [(field, value) for field in ("token_usage_before", "token_usage_after")
                 for value in (None, [], {}, "100", True, False, 0, -1, 1.5)]
        cases.extend(("delayed_recall_probes", value) for value in (None, [], {}, "probe"))
        for field, value in cases:
            with self.subTest(field=field, value=value):
                record = copy.deepcopy(self.artifact)
                record["evidence"]["context_memory"] = dict(memory, **{field: value})
                self.assertEqual(self.validate(record)["verdict"], "artifact_incomplete")

    def test_memory_increase_requires_numeric_quality_and_respects_efficiency_claim(self):
        self.artifact["scenario_requirements"]["context_memory"] = True
        memory = {"delayed_recall_probes": ["correct"],
                  "token_usage_before": 100, "token_usage_after": 120}
        for value in (None, True, [], {}, "better", 0, 0.5):
            with self.subTest(quality_delta=value):
                self.artifact["evidence"]["context_memory"] = dict(memory, quality_delta=value)
                expected = "artifact_complete" if type(value) in (int, float) else "artifact_incomplete"
                self.assertEqual(self.validate()["verdict"], expected)
        self.artifact["scenario_requirements"]["token_efficiency_claim"] = True
        self.assertEqual(self.validate()["verdict"], "artifact_incomplete")

    def test_recorded_schema_example_with_bundled_catalog_is_accepted(self):
        # Exercise real bundled cross-references, without consulting external artifacts.
        schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        catalog = json.loads((validator.ROOT / "data" / "skills_catalog.json").read_text(encoding="utf-8"))
        scenarios = json.loads((validator.ROOT / "data" / "benchmark_scenarios.json").read_text(encoding="utf-8"))
        source_scenarios = {row["id"] for row in scenarios
                            if row.get("dataset_track_id") == "source-skill-repository"}
        skill = next(row for row in catalog if source_scenarios.intersection(row["benchmark_scenarios"]))
        record = copy.deepcopy(schema["examples"][0])
        record.update(skill_id=skill["id"], source_commit=skill["commit_sha"],
                      source_repo=skill["source_repo"], source_path=skill["source_path"],
                      scenario_id=next(s for s in skill["benchmark_scenarios"] if s in source_scenarios))
        self.path.write_text(json.dumps(record), encoding="utf-8")
        result = validator.validate_artifact(self.path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_bad_json_and_non_object_roots_are_invalid(self):
        for text in ("{", "[]", "null", "42", '"text"'):
            with self.subTest(text=text):
                self.path.write_text(text, encoding="utf-8")
                result = validator.validate_artifact(self.path, self.catalog, self.scenarios)
                self.assertEqual(result["verdict"], "artifact_invalid")
                self.assertTrue(result["errors"])

    def test_cli_reports_structured_error_and_batch_finishes(self):
        self.artifact["skill_id"] = []
        self.validate()
        args = ["--catalog", str(self.catalog), "--scenarios", str(self.scenarios)]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = validator.main([str(self.path)] + args)
        self.assertIn(code, (1, 2))
        self.assert_rejected(json.loads(output.getvalue()), "/skill_id")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(validator.main(["--validate-all", str(self.base)] + args), 2)


if __name__ == "__main__":
    unittest.main()
