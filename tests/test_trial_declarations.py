import copy
from typing import Any

import _trial_declarations as target
import pytest


def test_declared_signatures_use_effective_prompt_and_workspace_not_metadata():
    first: dict[str, Any] = {
        "task": {"id": "first", "brief": "repair", "files": ["a.py", "b.py"]},
        "prompt_template": "Please <TASK_BRIEF>",
        "input_sha256": {"a.py": "a" * 64, "b.py": "b" * 64},
        "workspace_scaffold": {"tests.py": ""},
    }
    second = copy.deepcopy(first)
    second["task"]["id"] = "second"
    second["task"]["files"].reverse()
    second["task"]["brief"] = "unused"
    second["prompt_template"] = "Please repair"
    second["input_sha256"] = dict(reversed(list(second["input_sha256"].items())))
    assert target.declared_task_signatures(first) == target.declared_task_signatures(second)
    baseline, workspace = target.declared_task_signatures(first)
    second["prompt_template"] = "A different task"
    changed_task, same_workspace = target.declared_task_signatures(second)
    assert changed_task != baseline
    assert same_workspace == workspace
    second["input_sha256"]["a.py"] = "c" * 64
    changed_task, changed_workspace = target.declared_task_signatures(second)
    assert changed_workspace != workspace
    second["workspace_scaffold"]["tests.py"] = "changed"
    assert target.declared_task_signatures(second)[1] != changed_workspace


@pytest.mark.parametrize(
    "change",
    [
        {"task": {"brief": "", "files": ["fixture.py"]}},
        {"task": {"brief": "repair", "files": []}},
        {"task": {"brief": "repair", "files": ["fixture.py", "fixture.py"]}},
        {"input_sha256": {}},
        {"input_sha256": {"fixture.py": "A" * 64}},
        {"input_sha256": {"fixture.py": True}},
        {"prompt_template": ""},
        {"workspace_scaffold": {"fixture.py": "overlap"}},
        {"workspace_scaffold": {"output": 1}},
    ],
)
def test_declared_signatures_reject_incomplete_or_inconsistent_inputs(change):
    protocol = {
        "task": {"brief": "repair", "files": ["fixture.py"]},
        "input_sha256": {"fixture.py": "a" * 64},
        "prompt_template": "<TASK_BRIEF>",
    }
    protocol.update(change)
    with pytest.raises(ValueError, match="Task declaration"):
        target.declared_task_signatures(protocol)
