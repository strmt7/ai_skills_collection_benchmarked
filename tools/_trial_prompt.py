"""Check captured prompts against declared task text and skill hashes."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

INSTRUCTIONS = b"\n\nAdditional skill instructions for this condition:\n\n"
RUNTIME = b"<PYTHON_RUNTIME>"


def _matches_template(prompt: bytes, template: bytes) -> bool:
    parts = template.split(RUNTIME)
    count = len(parts) - 1
    if not count:
        return prompt == template
    extra = len(prompt) - sum(map(len, parts))
    if extra <= 0 or extra % count:
        return False
    length = extra // count
    runtime = prompt[len(parts[0]) : len(parts[0]) + length]
    try:
        path = runtime.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if "\x00" in path or not (PurePosixPath(path).is_absolute() or PureWindowsPath(path).is_absolute()):
        return False
    return template.replace(RUNTIME, runtime) == prompt


def _matches_skills(content: bytes, hashes: list[str]) -> bool:
    offset = 0
    for expected in hashes[:-1]:
        digest = hashlib.sha256()
        cursor = offset
        found = None
        while (boundary := content.find(b"\n\n", cursor)) != -1:
            digest.update(content[cursor:boundary])
            if digest.hexdigest() == expected:
                found = boundary
                break
            # Advance one byte so overlapping separators remain candidates.
            digest.update(content[boundary : boundary + 1])
            cursor = boundary + 1
        if found is None:
            return False
        offset = found + 2
    return bool(hashes) and hashlib.sha256(content[offset:]).hexdigest() == hashes[-1]


def _matches_prompt(prompt: bytes, template: bytes, hashes: list[str]) -> bool:
    if not hashes:
        return _matches_template(prompt, template)
    cursor = 0
    matches = 0
    while (boundary := prompt.find(INSTRUCTIONS, cursor)) != -1:
        if _matches_template(prompt[:boundary], template) and _matches_skills(
            prompt[boundary + len(INSTRUCTIONS) :], hashes
        ):
            matches += 1
        cursor = boundary + 1
    return matches == 1


def verify_prompt(raw: bytes, protocol: dict[str, Any], condition: str) -> None:
    """Verify the recorded prompt's declared content, without asserting delivery or authenticity."""
    task, template, conditions = protocol.get("task"), protocol.get("prompt_template"), protocol.get("conditions")
    if (
        not isinstance(task, dict)
        or not isinstance(task.get("brief"), str)
        or not isinstance(template, str)
        or not isinstance(conditions, dict)
        or not isinstance(conditions.get(condition), dict)
    ):
        raise ValueError("prompt protocol declaration is incomplete")
    skills = conditions[condition].get("skills")
    if not isinstance(skills, list) or any(
        not isinstance(skill, dict)
        or not isinstance(skill.get("path"), str)
        or not skill["path"]
        or not isinstance(skill.get("sha256"), str)
        or len(skill["sha256"]) != 64
        or any(char not in "0123456789abcdef" for char in skill["sha256"])
        for skill in skills
    ):
        raise ValueError("prompt protocol skill hashes are incomplete")
    hashes = [skill["sha256"] for skill in skills]
    expected = template.replace("<TASK_BRIEF>", task["brief"]).encode("utf-8")
    # write_text may add CR before each LF on Windows; reverse at most one layer.
    variants = {raw, raw.replace(b"\r\n", b"\n")}
    if not any(_matches_prompt(value, expected, hashes) for value in variants):
        raise ValueError("captured prompt disagrees with task or skill content in the protocol")
