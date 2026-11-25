"""Project only public task numbers and difficulty from the exact TestEval dataset."""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

root, target = map(Path, sys.argv[1:])
pin = json.loads((root / "testeval-calibration.freeze.json").read_bytes())
package = root / "testeval-exact-source"
dataset = (package / "data/leetcode-py.jsonl").read_bytes()
evaluator = (package / "eval_overall.py").read_bytes()
digest = lambda raw: hashlib.sha256(raw).hexdigest()
assert digest(dataset) == pin["dataset_sha256"]
assert digest(evaluator) == pin["evaluator_sha256"]
groups: dict[str, list[int]] = collections.defaultdict(list)
for line in dataset.splitlines():
    metadata = json.loads(line)
    key, difficulty = metadata["task_num"], metadata["difficulty"]
    assert type(key) is int and key > 0 and type(difficulty) is int and difficulty in {1, 2, 3}
    groups[str(difficulty)].append(key)
all_ids = [key for group in groups.values() for key in group]
assert len(all_ids) == len(set(all_ids)) == 210
assert pin["task_num"] in all_ids
frame = {
    "schema_version": 1,
    "publisher": {
        "repository": "https://github.com/LLM4SoftwareTesting/TestEval",
        "commit": pin["benchmark_commit"],
        "dataset_sha256": digest(dataset),
        "evaluator_sha256": digest(evaluator),
    },
    "selection_seed": "ai-skills-testeval-public-development-v1",
    "previous_exposures": [{"task_num": pin["task_num"], "reason": "Earlier hand-authored native grader control"}],
    "tasks_by_difficulty": {stratum: sorted(ids) for stratum, ids in groups.items()},
}
with target.open("x", encoding="utf-8", newline="\n") as output:
    output.write(json.dumps(frame, indent=2, sort_keys=True) + "\n")
print(json.dumps({"rows": len(all_ids), "strata": {key:len(value) for key,value in sorted(groups.items())},
                  "frame_sha256": digest(target.read_bytes())}))
