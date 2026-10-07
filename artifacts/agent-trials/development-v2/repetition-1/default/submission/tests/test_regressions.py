"""Regression checks for benchmark artifact structure and evidence validation."""

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


def set_field(record, parts, value):
    for part in parts[:-1]:
        record = record[part]
    record[parts[-1]] = value


def schema_fields(schema, parts=()):
    for name, child in schema.get("properties", {}).items():
        child_parts = (*parts, name)
        yield child_parts, child
        yield from schema_fields(child, child_parts)


class ArtifactRegressionTests(unittest.TestCase):
    def setUp(self):
        # Keep every generated fixture, subprocess output, and temporary file
        # inside this task workspace.
        self.temp = tempfile.TemporaryDirectory(prefix="validator-tests-", dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.schema = json.loads(validator.SCHEMA_PATH.read_text(encoding="utf-8"))
        self.record = copy.deepcopy(self.schema["examples"][0])
        self.record["runner"]["batch_name"] = "regression"
        self.record["evidence"]["visual"] = {}
        self.record["evidence"]["context_memory"] = {}
        self.artifact_path = self.base / "artifact.json"
        self.catalog_path = self.base / "catalog.json"
        self.scenarios_path = self.base / "scenarios.json"
        self.write_json(self.catalog_path, [{
            "id": self.record["skill_id"],
            "commit_sha": self.record["source_commit"],
            "source_repo": self.record["source_repo"],
            "source_path": self.record["source_path"],
            "benchmark_scenarios": [self.record["scenario_id"], "external-task"],
        }])
        self.write_json(self.scenarios_path, [
            {"id": self.record["scenario_id"], "dataset_track_id": "source-skill-repository"},
            {"id": "external-task", "dataset_track_id": "external-fixture"},
        ])
        (self.base / "transcript.txt").write_text("Recorded commands\n", encoding="utf-8")
        self.write_json(self.base / "result.json", {"recorded": True})
        (self.base / "directory").mkdir()

    @staticmethod
    def write_json(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def validate(self, record=None):
        self.write_json(self.artifact_path, self.record if record is None else record)
        return validator.validate_artifact(
            self.artifact_path, self.catalog_path, self.scenarios_path
        )

    def assert_rejected(self, result, pointer=None):
        self.assertIn(result["verdict"], {"artifact_invalid", "artifact_incomplete"})
        self.assertTrue(result["errors"])
        self.assertIsInstance(result["warnings"], list)
        if pointer:
            self.assertTrue(
                any(pointer in error for error in result["errors"]), result
            )

    def make_independent(self):
        self.record["artifact_kind"] = "independent_benchmark"
        self.record["scenario_id"] = "external-task"
        self.record["independence"].update({
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
        })

    def add_visual(self):
        self.record["scenario_requirements"]["visual_or_browser"] = True
        (self.base / "screen.png").write_bytes(b"recorded screenshot fixture")
        self.record["evidence"]["visual"] = {
            "screenshot_paths": ["screen.png"],
            "website_url_or_mirror": "https://example.invalid/recorded",
            "viewport": {"width": 1280, "height": 720},
        }

    def add_memory(self):
        self.record["scenario_requirements"].update({
            "context_memory": True, "token_efficiency_claim": True,
        })
        self.record["evidence"]["context_memory"] = {
            "delayed_recall_probes": [{"question": "fixture", "correct": True}],
            "token_usage_before": 100,
            "token_usage_after": 80,
            "quality_delta": 0.0,
        }

    def test_complete_provenance_and_permitted_extra_metadata(self):
        self.record["custom_metadata"] = {"anything": [None, True, {"nested": 3}]}
        for name in ("runner", "scenario_requirements", "input_snapshot", "execution",
                     "outputs", "metrics", "independence", "evidence"):
            self.record[name]["extra_metadata"] = {"recorded": [1, 2, 3]}
        before = copy.deepcopy(self.record)
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_complete", result)
        self.assertEqual(result["errors"], [])
        self.assertTrue(any("provenance_check" in warning for warning in result["warnings"]))
        self.assertEqual(json.loads(self.artifact_path.read_text(encoding="utf-8")), before)

    def test_complete_recorded_independent_visual_and_memory_artifact(self):
        self.make_independent()
        self.add_visual()
        self.add_memory()
        result = self.validate()
        self.assertEqual(result, {"verdict": "artifact_complete", "errors": [], "warnings": []})

    def test_complete_record_with_workspace_catalog_and_scenarios(self):
        catalog = json.loads((ROOT / "data" / "skills_catalog.json").read_text(encoding="utf-8"))
        scenarios = {s["id"]: s for s in json.loads(
            (ROOT / "data" / "benchmark_scenarios.json").read_text(encoding="utf-8")
        )}
        skill = catalog[0]
        self.record.update({
            "skill_id": skill["id"], "source_commit": skill["commit_sha"],
            "source_repo": skill["source_repo"], "source_path": skill["source_path"],
            "scenario_id": next(s for s in skill["benchmark_scenarios"] if s in scenarios),
        })
        self.write_json(self.artifact_path, self.record)
        result = validator.validate_artifact(self.artifact_path)
        self.assertEqual(result["verdict"], "artifact_complete", result)

    def test_wrong_types_for_every_schema_field_return_structured_errors(self):
        wrong_values = {
            "object": [None, [], "wrong", 1, True],
            "array": [None, {}, "wrong", 1, True],
            "string": [None, {}, [], 1, True],
            "boolean": [None, {}, [], "true", 1],
        }
        for parts, field_schema in schema_fields(self.schema):
            for value in wrong_values[field_schema["type"]]:
                with self.subTest(field=parts, value=value):
                    record = copy.deepcopy(self.record)
                    set_field(record, parts, value)
                    self.assert_rejected(self.validate(record), "/" + "/".join(parts))

    def test_schema_min_length_applies_to_every_declared_string(self):
        for parts, field_schema in schema_fields(self.schema):
            if "minLength" not in field_schema:
                continue
            with self.subTest(field=parts):
                record = copy.deepcopy(self.record)
                set_field(record, parts, "")
                self.assert_rejected(self.validate(record), "/" + "/".join(parts))

    def test_multiple_structural_errors_are_reported_together(self):
        self.record.update({"artifact_kind": {}, "skill_id": [], "input_snapshot": None})
        self.record["runner"]["tool"] = ""
        result = self.validate()
        self.assertEqual(result["verdict"], "artifact_invalid")
        for pointer in ("/artifact_kind", "/skill_id", "/input_snapshot", "/runner/tool"):
            self.assert_rejected(result, pointer)

    def test_required_fields_at_every_schema_object(self):
        objects = [((), self.schema)] + list(schema_fields(self.schema))
        for parts, object_schema in objects:
            for name in object_schema.get("required", []):
                with self.subTest(parent=parts, missing=name):
                    record = copy.deepcopy(self.record)
                    parent = record
                    for part in parts:
                        parent = parent[part]
                    del parent[name]
                    self.assert_rejected(self.validate(record), "/" + "/".join((*parts, name)))

    def test_schema_array_constraints_and_item_types(self):
        fields = [
            ("evidence", "artifact_paths"), ("evidence", "citations_or_paths"),
            ("objective_checks",),
        ]
        for parts in fields:
            for value in ([], [""], [None], [{}], [[]], [True], [1]):
                with self.subTest(field=parts, value=value):
                    record = copy.deepcopy(self.record)
                    set_field(record, parts, value)
                    self.assert_rejected(self.validate(record), "/" + "/".join(parts))

    def test_schema_enum_and_patterns(self):
        cases = [
            ("artifact_version", "2.0"), ("artifact_kind", "passed"),
            ("catalog_commit", "a" * 39), ("catalog_commit", "A" * 40),
            ("source_commit", "z" * 40),
        ]
        for name, value in cases:
            with self.subTest(field=name, value=value):
                record = copy.deepcopy(self.record)
                record[name] = value
                self.assert_rejected(self.validate(record), "/" + name)

    def test_unavailable_schema_rejects_complete_record(self):
        for contents in (None, "{bad JSON", "[]"):
            with self.subTest(contents=contents):
                schema_path = self.base / "unavailable.schema.json"
                if contents is None:
                    schema_path.unlink(missing_ok=True)
                else:
                    schema_path.write_text(contents, encoding="utf-8")
                with patch.object(validator, "SCHEMA_PATH", schema_path):
                    result = self.validate()
                self.assert_rejected(result)
                self.assertTrue(any("schema" in error.lower() for error in result["errors"]), result)
        with patch.object(validator, "SCHEMA_PATH", self.base / "directory"):
            self.assert_rejected(self.validate())

    def test_additional_properties_policy_and_pointer_escaping(self):
        schema = copy.deepcopy(self.schema)
        schema["properties"]["runner"]["additionalProperties"] = False
        self.record["runner"]["extra/key~"] = "metadata"
        with patch.object(validator, "_load_schema", return_value=schema):
            self.assert_rejected(self.validate(), "/runner/extra~1key~0")
        schema["properties"]["runner"]["additionalProperties"] = {"type": "string", "minLength": 1}
        with patch.object(validator, "_load_schema", return_value=schema):
            self.assertEqual(self.validate()["verdict"], "artifact_complete")
            self.record["runner"]["extra/key~"] = 3
            self.assert_rejected(self.validate(), "/runner/extra~1key~0")

    def test_paths_must_be_files(self):
        self.add_visual()
        for parts, value in [
            (("execution", "commands_or_transcript_path"), "directory"),
            (("evidence", "artifact_paths"), ["directory"]),
            (("evidence", "visual", "screenshot_paths"), ["directory"]),
        ]:
            with self.subTest(field=parts):
                record = copy.deepcopy(self.record)
                set_field(record, parts, value)
                self.assert_rejected(self.validate(record))

    def test_bad_filesystem_paths_do_not_raise(self):
        self.add_visual()
        for parts in [
            ("execution", "commands_or_transcript_path"),
            ("evidence", "artifact_paths"),
            ("evidence", "visual", "screenshot_paths"),
        ]:
            for bad_path in ("missing.txt", "bad\x00path", "x" * 5000):
                with self.subTest(field=parts, value=bad_path[:20]):
                    record = copy.deepcopy(self.record)
                    set_field(record, parts, bad_path if parts[0] == "execution" else [bad_path])
                    self.assert_rejected(self.validate(record))

    def test_absolute_and_workspace_relative_file_paths_still_work(self):
        self.record["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        self.record["evidence"]["artifact_paths"] = [
            (self.base / "result.json").relative_to(ROOT).as_posix()
        ]
        self.assertEqual(self.validate()["verdict"], "artifact_complete")

    def test_domain_invariants_remain_enforced(self):
        self.make_independent()
        cases = [
            (("execution", "fresh_session"), False),
            (("input_snapshot", "is_real"), False),
            (("independence", "task_defined_outside_skill"), False),
            (("independence", "uses_exact_skill_content_for_expected_result"), True),
            (("skill_id",), "unknown-skill"), (("scenario_id",), "unknown-scenario"),
            (("source_commit",), "a" * 40), (("benchmark_status",), "passed"),
            (("verdict",), "passed"),
        ]
        for parts, value in cases:
            with self.subTest(field=parts):
                record = copy.deepcopy(self.record)
                set_field(record, parts, value)
                self.assert_rejected(self.validate(record))

    def test_malformed_visual_and_memory_values_return_errors(self):
        self.add_visual()
        self.add_memory()
        cases = [
            (("evidence", "visual", "screenshot_paths"), [None]),
            (("evidence", "visual", "viewport"), []),
            (("evidence", "context_memory", "delayed_recall_probes"), {}),
            (("evidence", "context_memory", "token_usage_before"), "100"),
            (("evidence", "context_memory", "token_usage_after"), True),
        ]
        for parts, value in cases:
            with self.subTest(field=parts):
                record = copy.deepcopy(self.record)
                set_field(record, parts, value)
                self.assert_rejected(self.validate(record))

    def test_unreadable_json_and_wrong_root_return_invalid(self):
        for value in (None, [], "wrong", 3, True):
            with self.subTest(root=value):
                self.write_json(self.artifact_path, value)
                self.assertEqual(validator.validate_artifact(self.artifact_path)["verdict"], "artifact_invalid")
        for text in ("{broken JSON", "null"):
            self.artifact_path.write_text(text, encoding="utf-8")
            self.assertEqual(validator.validate_artifact(self.artifact_path)["verdict"], "artifact_invalid")
        self.artifact_path.unlink()
        self.assertEqual(validator.validate_artifact(self.artifact_path)["verdict"], "artifact_invalid")

    def test_cli_reports_json_and_exit_codes_without_tracebacks(self):
        cases = [(self.record, "artifact_complete", 0)]
        malformed = copy.deepcopy(self.record)
        malformed["skill_id"] = []
        cases.append((malformed, "artifact_invalid", 1))
        incomplete = copy.deepcopy(self.record)
        incomplete["execution"]["commands_or_transcript_path"] = "missing.txt"
        cases.append((incomplete, "artifact_incomplete", 2))
        for record, verdict, exit_code in cases:
            with self.subTest(verdict=verdict):
                self.write_json(self.artifact_path, record)
                result = subprocess.run([
                    sys.executable, str(ROOT / "tools" / "check_benchmark_artifact.py"),
                    str(self.artifact_path), "--catalog", str(self.catalog_path),
                    "--scenarios", str(self.scenarios_path),
                ], capture_output=True, text=True, cwd=ROOT)
                self.assertEqual(result.returncode, exit_code, result.stderr)
                self.assertEqual(json.loads(result.stdout)["verdict"], verdict)
                self.assertNotIn("Traceback", result.stderr)

    def test_batch_continues_past_malformed_artifact(self):
        broken = self.base / "broken"
        good = self.base / "good"
        broken.mkdir()
        good.mkdir()
        record = copy.deepcopy(self.record)
        record["artifact_kind"] = {}
        self.write_json(broken / "artifact.json", record)
        complete = copy.deepcopy(self.record)
        complete["execution"]["commands_or_transcript_path"] = str(self.base / "transcript.txt")
        complete["evidence"]["artifact_paths"] = [str(self.base / "result.json")]
        self.write_json(good / "artifact.json", complete)
        total, failed, failures = validator._validate_all(
            self.base, self.catalog_path, self.scenarios_path
        )
        self.assertEqual((total, failed), (2, 1))
        self.assertEqual(failures[0][0], broken / "artifact.json")
        self.assert_rejected(failures[0][1])


if __name__ == "__main__":
    unittest.main()
