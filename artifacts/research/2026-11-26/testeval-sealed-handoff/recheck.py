"""Regrade the sealed public TestEval controls without a browser or container."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

from _trial_transcript import strict_json  # noqa: E402
from grade_testeval_submission import CAPTURE_EVIDENCE, TEST_SUBMISSION, grade  # noqa: E402
from validate_testeval_calibration import read_evidence  # noqa: E402

DIRECTORY = Path(__file__).resolve().parent
NATIVE_NAME = re.compile(r"[a-z0-9][a-z0-9-]*\.(?:xml|stdout)")


def recheck(path: Path) -> dict[str, dict]:
    archive = strict_json(read_evidence(path).decode("utf-8"))
    study = strict_json(archive["study_plan"])
    controls = archive["controls"]
    if archive["schema_version"] != 1 or study["model_attempts"] != 0 or controls.keys() != study["expected"].keys():
        raise ValueError("Sealed control archive differs from the prospective study plan")

    outcomes = {}
    with TemporaryDirectory() as directory:
        for index, (name, item) in enumerate(controls.items()):
            records = item["records"]
            capture = strict_json(records["capture.json"])
            refs = [
                capture["publisher"]["stdout"],
                *(row["junit"] for row in capture["variants"].values()),
            ]
            report_names = {ref["file"] for ref in refs if ref is not None}
            required = {"capture.json", "plan.json", TEST_SUBMISSION, *CAPTURE_EVIDENCE.values()}
            if records.keys() != required | report_names or any(not NATIVE_NAME.fullmatch(s) for s in report_names):
                raise ValueError(f"Unexpected native evidence inventory for {name}")
            target = Path(directory) / str(index)
            target.mkdir()
            for filename, raw in records.items():
                (target / filename).write_bytes(raw.encode("utf-8"))
            result = grade((target / "plan.json").read_bytes(), target / "capture.json")
            if result != item["grade"] or result["task_id"] != study["task_id"]:
                raise ValueError(f"Replayed seal grade differs for {name}")
            observation = {
                "exit": item["controller_exit"],
                "reference": result["reference"]["status"],
                "cases": len(result["reference_pytest_cases"] or ()),
                "detected": result["sensitivity"]["detected"],
                "inconclusive": result["sensitivity"]["inconclusive"],
            }
            if observation != study["expected"][name]:
                raise ValueError(f"Observed outcome differs from the frozen control for {name}")
            outcomes[name] = observation
    return outcomes


def main() -> int:
    outcomes = recheck(DIRECTORY / "native-reports.json")
    print(json.dumps({"controls": len(outcomes), "outcomes": outcomes, "model_attempts": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
