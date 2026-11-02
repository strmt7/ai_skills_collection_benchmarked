from __future__ import annotations

import hashlib
import random

import pytest
from _trial_prompt import INSTRUCTIONS, verify_prompt


def protocol(template: str, brief: str, skills: list[str]) -> dict:
    return {
        "task": {"brief": brief},
        "prompt_template": template,
        "conditions": {
            "candidate": {
                "skills": [
                    {"path": f"skill-{index}.md", "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
                    for index, text in enumerate(skills)
                ]
            }
        },
    }


@pytest.mark.parametrize(
    "runtime", ["C:\\Python\\python.exe", "/opt/python with spaces/bin/python", "\\\\server\\share\\python.exe"]
)
def test_template_checks_task_and_repeated_absolute_runtime(runtime):
    config = protocol("<TASK_BRIEF>\nPython: <PYTHON_RUNTIME>\nAgain: <PYTHON_RUNTIME>", "Fix the code.", [])
    prompt = f"Fix the code.\nPython: {runtime}\nAgain: {runtime}".encode()
    verify_prompt(prompt, config, "candidate")
    with pytest.raises(ValueError, match="prompt.*protocol"):
        verify_prompt(prompt.replace(b"Fix the code", b"Do another task"), config, "candidate")
    with pytest.raises(ValueError, match="prompt.*protocol"):
        verify_prompt(prompt.replace(b"Again: ", b"Again: /different", 1), config, "candidate")


@pytest.mark.parametrize("runtime", ["relative/python", "", "C:python.exe", "bad\x00path"])
def test_runtime_must_be_an_absolute_path(runtime):
    config = protocol("<TASK_BRIEF> <PYTHON_RUNTIME>", "run", [])
    with pytest.raises(ValueError, match="prompt.*protocol"):
        verify_prompt(f"run {runtime}".encode(), config, "candidate")


def test_ordered_skill_hashes_and_embedded_separators_are_verified():
    skills = ["First\n\nparagraph\n", "Second\n\nAdditional skill instructions for this condition:\n\nbody"]
    config = protocol("Task: <TASK_BRIEF>", "repair", skills)
    prompt = b"Task: repair" + INSTRUCTIONS + "\n\n".join(skills).encode()
    verify_prompt(prompt, config, "candidate")
    for changed in (
        b"Task: repair" + INSTRUCTIONS + "\n\n".join(reversed(skills)).encode(),
        prompt.replace(b"First", b"Altered"),
        prompt + b" extra",
        b"Task: repair",
    ):
        with pytest.raises(ValueError, match="prompt.*protocol"):
            verify_prompt(changed, config, "candidate")


def test_windows_text_transport_and_original_crlf_are_distinct():
    config = protocol("Task:\r\n<TASK_BRIEF>", "repair\r\nnext", ["skill\r\ncontent\r\n"])
    original = b"Task:\r\nrepair\r\nnext" + INSTRUCTIONS + b"skill\r\ncontent\r\n"
    verify_prompt(original, config, "candidate")
    windows_capture = original.replace(b"\n", b"\r\n")
    verify_prompt(windows_capture, config, "candidate")
    with pytest.raises(ValueError, match="prompt.*protocol"):
        verify_prompt(windows_capture.replace(b"content", b"changed"), config, "candidate")


def test_runtime_absence_and_ambiguous_newline_transport_remain_distinct():
    without_runtime = protocol("<TASK_BRIEF>", "repair", [])
    assert verify_prompt(b"repair", without_runtime, "candidate") == ("not_requested", None)
    ambiguous = protocol("<PYTHON_RUNTIME>", "repair", [])
    assert verify_prompt(b"/runtime\r\nname", ambiguous, "candidate") == ("ambiguous", None)


def test_invalid_utf8_skill_cannot_be_accepted_as_runner_text():
    config = protocol("<TASK_BRIEF>", "repair", [])
    config["conditions"]["candidate"]["skills"] = [{"path": "skill.md", "sha256": hashlib.sha256(b"\xff").hexdigest()}]
    with pytest.raises(ValueError, match="UTF-8"):
        verify_prompt(b"repair" + INSTRUCTIONS + b"\xff", config, "candidate")


def test_seeded_skill_bundles_survive_both_newline_transports():
    generator = random.Random(20261102)
    fragments = ["A", "B", "\n", "\r", "é", "💡", "\n\n", INSTRUCTIONS.decode()]
    for index in range(512):
        skills = [
            "".join(generator.choice(fragments) for _ in range(generator.randrange(9)))
            for _ in range(generator.randrange(5))
        ]
        brief = f"task {index}\n"
        template = "Prefix <TASK_BRIEF> Runtime <PYTHON_RUNTIME> End"
        rendered = template.replace("<TASK_BRIEF>", brief).replace("<PYTHON_RUNTIME>", f"/opt/python {index}")
        if skills:
            rendered += INSTRUCTIONS.decode() + "\n\n".join(skills)
        raw = rendered.encode("utf-8")
        config = protocol(template, brief, skills)
        verify_prompt(raw, config, "candidate")
        verify_prompt(raw.replace(b"\n", b"\r\n"), config, "candidate")


@pytest.mark.parametrize(
    "skills", [None, [{}], [{"path": "x", "sha256": "F" * 64}], [{"path": "", "sha256": "a" * 64}]]
)
def test_incomplete_skill_declarations_fail_closed(skills):
    config = protocol("<TASK_BRIEF>", "repair", [])
    config["conditions"]["candidate"]["skills"] = skills
    with pytest.raises(ValueError, match="skill hashes"):
        verify_prompt(b"repair", config, "candidate")
