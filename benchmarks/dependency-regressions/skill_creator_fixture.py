"""Trusted package controls; no AI process, provider, or candidate task is run."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import traceback
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path[:0] = ["/submission/original", "/submission/vendor"]


def run(request):
    try:
        return run_controls(request)
    except Exception as exc:
        raise RuntimeError(traceback.format_exc()) from exc


def run_controls(request):
    from scripts import aggregate_benchmark as aggregate
    from scripts import package_skill, quick_validate, run_eval, run_loop, utils

    checks = []
    observations = {}
    with tempfile.TemporaryDirectory(prefix="skill-creator-controls-", dir="/tmp") as temporary:
        root = Path(temporary)

        def grade(directory, value):
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "grading.json").write_text(json.dumps(value), encoding="utf-8")

        valid = {
            "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
            "expectations": [{"text": "Owned fixture value matches", "passed": True, "evidence": "fixture"}],
        }
        benchmark = root / "missing"
        grade(benchmark / "eval-0/with_skill/run-1", valid)
        (benchmark / "eval-0/with_skill/run-2").mkdir()
        with contextlib.redirect_stdout(io.StringIO()):
            loaded = aggregate.load_run_results(benchmark)
        summary = aggregate.aggregate_results(loaded)
        assert len(loaded["with_skill"]) == 1 and summary["with_skill"]["pass_rate"]["mean"] == 1.0
        observations["missing_run"] = {"planned_directories": 2, "counted_runs": 1, "reported_pass_rate": 1.0}
        checks.append("ungraded_planned_run_omitted_from_denominator")

        direct = root / "documented-layout"
        grade(direct / "eval-0/with_skill", valid)
        assert aggregate.load_run_results(direct) == {}
        checks.append("entrypoint_direct_grading_layout_not_aggregated")

        character = root / "characters"
        grade(character / "eval-0/with_skill/run-1", {**valid, "execution_metrics": {"output_chars": 913}})
        assert aggregate.load_run_results(character)["with_skill"][0]["tokens"] == 913
        checks.append("output_characters_reported_as_tokens")

        timing = root / "timing"
        run_dir = timing / "eval-0/with_skill/run-1"
        grade(run_dir, {**valid, "timing": {"total_duration_seconds": 1.0}})
        (run_dir / "timing.json").write_text(json.dumps({"total_duration_seconds": 1.0, "total_tokens": 47}))
        assert aggregate.load_run_results(timing)["with_skill"][0]["tokens"] == 0
        checks.append("nonzero_embedded_duration_discards_sibling_token_usage")

        inconsistent = root / "contradictory"
        grade(
            inconsistent / "eval-0/with_skill/run-1",
            {
                "summary": {"passed": 0, "failed": 1, "total": 1, "pass_rate": 1.5},
                "expectations": [{"text": "Fixture is wrong", "passed": False, "evidence": "fixture"}],
            },
        )
        contradictory = aggregate.generate_benchmark(inconsistent)
        assert contradictory["run_summary"]["with_skill"]["pass_rate"]["mean"] == 1.5
        assert contradictory["metadata"]["runs_per_configuration"] == 3 and len(contradictory["runs"]) == 1
        observations["invalid_score"] = {
            "failed_expectations": 1,
            "reported_pass_rate": 1.5,
            "actual_runs": 1,
            "metadata_runs_per_configuration": 3,
        }
        checks.append("contradictory_out_of_range_score_and_fixed_repetition_metadata_accepted")

        skill = root / "fixture-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text("---\nname: ''\ndescription: ''\n---\nOwned fixture.\n", encoding="utf-8")
        assert quick_validate.validate_skill(skill)[0] is True
        checks.append("empty_required_frontmatter_values_accepted")
        (skill / "SKILL.md").write_text(
            "---\nname: fixture-skill\ndescription: |\n  line one\n  line two\n---\nOwned fixture.\n", encoding="utf-8"
        )
        assert utils.parse_skill_md(skill)[1] == "line one line two"
        checks.append("literal_yaml_block_description_newlines_changed")

        outside = root / "outside-owned.txt"
        outside.write_text("OWNED_OUTSIDE_PACKAGE_SENTINEL", encoding="utf-8")
        (skill / "linked.txt").symlink_to(outside)
        with contextlib.redirect_stdout(io.StringIO()):
            archive = package_skill.package_skill(skill, root / "archives")
        assert archive is not None
        with zipfile.ZipFile(archive) as zipped:
            assert zipped.read("fixture-skill/linked.txt") == b"OWNED_OUTSIDE_PACKAGE_SENTINEL"
        checks.append("packager_follows_link_outside_selected_package")

        evals = [{"query": f"owned-positive-{i}", "should_trigger": True} for i in range(5)]
        evals += [{"query": f"owned-negative-{i}", "should_trigger": False} for i in range(5)]
        train, test = run_loop.split_eval_set(evals, 0.4)
        train_names = {item["query"] for item in train}
        original_eval, original_improve, original_root = (
            run_loop.run_eval,
            run_loop.improve_description,
            run_loop.find_project_root,
        )
        calls = []

        def controlled_eval(**kwargs):
            # Deterministic injected evaluator results qualify selection logic only.
            iteration = len(calls) + 1
            calls.append(kwargs["description"])
            rows = []
            for item in kwargs["eval_set"]:
                is_train = item["query"] in train_names
                passed = is_train and item["query"] != train[0]["query"] if iteration == 2 else not is_train
                rows.append({**item, "pass": passed, "runs": 1, "triggers": int(passed == item["should_trigger"])})
            return {"results": rows}

        run_loop.run_eval = controlled_eval
        run_loop.improve_description = lambda **kwargs: "owned-candidate-two"
        run_loop.find_project_root = lambda: root
        try:
            output = run_loop.run_loop(
                evals, skill, "owned-candidate-one", 1, 2, 2, 1, 0.5, 0.4, "NO_MODEL_CALL", False
            )
            assert output["best_description"] == "owned-candidate-one"
            assert output["history"][1]["train_passed"] > output["history"][0]["train_passed"]
            assert output["history"][0]["test_passed"] == len(test) and output["history"][1]["test_passed"] == 0
            observations["selection"] = {
                "selected_candidate": 1,
                "better_training_candidate": 2,
                "selection_uses_repeated_validation_scores": True,
            }
            checks.append("reported_test_set_used_for_candidate_selection")

            duplicates = [{"query": "owned-duplicate", "should_trigger": label} for label in [True, True, False, False]]
            output = run_loop.run_loop(
                duplicates, skill, "owned-duplicate-candidate", 1, 2, 1, 1, 0.5, 0.4, "NO_MODEL_CALL", False
            )
            assert output["test_size"] == 2 and output["history"][0]["test_total"] == 0
            checks.append("duplicate_query_text_moves_declared_test_rows_into_training_results")
        finally:
            run_loop.run_eval, run_loop.improve_description, run_loop.find_project_root = (
                original_eval,
                original_improve,
                original_root,
            )

        tiny_train, tiny_test = run_loop.split_eval_set(
            [
                {"query": "owned-one-positive", "should_trigger": True},
                {"query": "owned-one-negative", "should_trigger": False},
            ],
            0.4,
        )
        assert len(tiny_train) == 0 and len(tiny_test) == 2
        checks.append("small_stratified_split_leaves_no_training_rows")

        # The image has no Claude CLI or credentials. Its IPC restrictions do not
        # provide multiprocessing semaphores. Adapt dispatch only; exercise the
        # unchanged query function and unchanged future/error/scoring logic.
        assert shutil.which("claude") is None
        original_executor = run_eval.ProcessPoolExecutor
        run_eval.ProcessPoolExecutor = ThreadPoolExecutor
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                missing = run_eval.run_eval(
                    [{"query": "owned-no-trigger", "should_trigger": False}],
                    "fixture-skill",
                    "Owned fixture description",
                    1,
                    2,
                    root / "missing-cli",
                    1,
                )
        finally:
            run_eval.ProcessPoolExecutor = original_executor
        assert missing["summary"]["passed"] == 1 and missing["results"][0]["triggers"] == 0
        checks.append("missing_model_cli_counted_as_correct_negative_trigger")

    return {
        "platform": sys.platform,
        "uid": os.getuid(),
        "checks": checks,
        "observations": observations,
        "ai_processes_launched": 0,
        "provider_calls": 0,
        "failed_launch_dispatch_adapter": "native ThreadPoolExecutor; unchanged query and result accounting",
        "fixture_temporary_directory_removed": not root.exists(),
    }
