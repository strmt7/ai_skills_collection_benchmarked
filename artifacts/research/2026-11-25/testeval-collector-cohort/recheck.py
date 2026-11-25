"""Replay the archived public TestEval controller outputs through the production grader."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

from _trial_transcript import strict_json  # noqa: E402
from grade_testeval_submission import grade, sha256  # noqa: E402

HERE = Path(__file__).resolve().parent
SELECTION = ROOT / "benchmarks/agent-effectiveness/development/testeval-pilot-v2/selection.json"
CONTROLS = ("exact", "shape", "incorrect")
REPORT_NAME = re.compile(r"[a-zA-Z0-9_-]+\.(?:xml|stdout)")


def verify(directory: Path) -> dict[str, Any]:
    selection = SELECTION.read_bytes()
    frozen = strict_json(selection.decode("utf-8"))
    tasks = {task["task_num"] for task in frozen["selected"]}
    publisher = frozen["publisher"]
    source = {
        "commit_sha": publisher["commit"],
        "dataset_sha256": publisher["dataset_sha256"],
        "evaluator_sha256": publisher["evaluator_sha256"],
    }
    expected = {(task, arm) for task in tasks for arm in CONTROLS}
    with (directory / "native-reports.json").open("rb") as stream:
        raw = stream.read(2 * 1024**2 + 1)
    if len(raw) > 2 * 1024**2:
        raise ValueError("Archived public control bundle exceeds 2 MiB")
    archive = strict_json(raw.decode("utf-8"))
    if (
        archive.keys() != {"schema_version", "model_attempts", "study_plan", "controls"}
        or type(archive["schema_version"]) is not int
        or archive["schema_version"] != 1
        or type(archive["model_attempts"]) is not int
        or archive["model_attempts"] != 0
        or len(archive["controls"]) != len(expected)
    ):
        raise ValueError("Invalid frozen public TestEval control bundle")

    study_plan_bytes = archive["study_plan"].encode("utf-8")
    study_plan = strict_json(archive["study_plan"])
    schedule = study_plan["planned_attempts"]
    if (
        study_plan["kind"] != "public_development_model_free_controls"
        or type(study_plan["model_attempts"]) is not int
        or study_plan["model_attempts"] != 0
        or study_plan["selection_sha256"] != sha256(selection)
        or len(schedule) != len(expected)
        or {(run["task"], run["control"]) for run in schedule} != expected
    ):
        raise ValueError("Study plan differs from the frozen public selection")

    grades = {}
    fixtures = {}
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        for index, (record, scheduled) in enumerate(zip(archive["controls"], schedule, strict=True)):
            case = (record["task"], record["control"])
            plan_bytes = record["plan"].encode("utf-8")
            if (
                case != (scheduled["task"], scheduled["control"])
                or scheduled["case_key"] != f"{case[0]}-{case[1]}"
                or scheduled["plan_sha256"] != sha256(plan_bytes)
            ):
                raise ValueError(f"Archived public control differs from the study plan for {case}")
            plan = strict_json(record["plan"])
            fixture = plan["programs"], plan["pytest_cases"]
            if plan["publisher"] != source or fixture != fixtures.setdefault(case[0], fixture):
                raise ValueError(f"Publisher or comparison fixtures differ for {case}")
            native = strict_json(record["capture"])
            declared = [
                native["publisher"]["stdout"],
                *(row["junit"] for row in native["variants"].values()),
            ]
            reports = record["reports"]
            if set(reports) != {report["file"] for report in declared if report is not None}:
                raise ValueError(f"Archived report inventory differs for {case}")
            trial = root / str(index)
            trial.mkdir()
            capture = trial / "capture.json"
            capture.write_bytes(record["capture"].encode("utf-8"))
            for name, content in reports.items():
                if REPORT_NAME.fullmatch(name) is None:
                    raise ValueError(f"Invalid archived report name {name}")
                (trial / name).write_bytes(content.encode("utf-8"))
            result = grade(plan_bytes, capture)
            if result["task_id"] != record["task"]:
                raise ValueError(f"Grade does not address declared public task {case}")
            grades[case] = result
    if set(grades) != expected:
        raise ValueError("Frozen public control bundle omits a comparison")

    measurements = {}
    for arm in CONTROLS:
        group = [grades[(task, arm)] for task in sorted(tasks)]
        references = Counter(item["reference"]["status"] for item in group)
        publisher = Counter(item["native_test_eval"]["status"] for item in group)
        measurable = [item["sensitivity"] for item in group if item["sensitivity"]["detected"] is not None]
        measurements[arm] = {
            "reference": dict(references),
            "publisher": dict(publisher),
            "measurable_defect_runs": len(measurable),
            "detected": sum(item["detected"] for item in measurable) if measurable else None,
            "survived": sum(item["survived"] for item in measurable) if measurable else None,
            "inconclusive": sum(item["inconclusive"] for item in measurable) if measurable else None,
            "planned_defects": sum(item["sensitivity"]["planned"] for item in group),
        }

    equal_metrics = []
    for task in sorted(tasks):
        observed = [grades[(task, arm)]["native_test_eval"]["metrics"] for arm in CONTROLS]
        if observed[0] is not None and observed[0] == observed[1] == observed[2]:
            equal_metrics.append(task)
    return {
        "schema_version": 1,
        "selection_sha256": sha256(selection),
        "study_plan_sha256": sha256(study_plan_bytes),
        "bundle_sha256": sha256(raw),
        "public_tasks": len(tasks),
        "control_runs": len(grades),
        "identical_native_metric_task_ids": equal_metrics,
        "observations": measurements,
        "model_attempts": 0,
    }


def main() -> int:
    try:
        result = verify(HERE)
        stored = strict_json((HERE / "summary.json").read_text(encoding="utf-8"))
        if result != stored:
            raise ValueError("Published summary differs from regraded native reports")
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "public_tasks": result["public_tasks"],
                "control_runs": result["control_runs"],
                "model_attempts": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
