"""Verify a ComfyUI model recommendation against captured Anthropic lifecycle data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SKILL = "included/skills/by-category/devops-cloud-operations/creative-reference/twwch-comfyui-workflow-skill/SKILL.md"
SKILL_HASH = "3dd6746ab187a97c8f5493be5ac2820fbfd523104d2494fb6af811cfd3dfb024"
NATIVE_HASH = "501ed060c1b99f3d08739485509d15cd43cf449f6c59b4767ae61c670339def1"
MODEL = "claude-sonnet-4-20250514"


def read(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected source bytes: {path.name}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--anthropic-native", type=Path, required=True)
    args = parser.parse_args()
    skill = read(args.root / SKILL, SKILL_HASH).decode("utf-8")
    page = json.loads(read(args.anthropic_native, NATIVE_HASH))
    if (
        page["url"] != "https://platform.claude.com/docs/en/about-claude/model-deprecations"
        or page["status_code"] != 200
        or page["success"] is not True
    ):
        raise ValueError("Unexpected Anthropic page scope or status")
    rows = [
        line.strip()
        for line in page["markdown"]["raw_markdown"].splitlines()
        if re.match(r"^\|\s*claude-sonnet-4-20250514\s*\|", line)
    ]
    if len(rows) != 1 or not re.search(r"\|\s*Retired\s*\|", rows[0]) or "June 15, 2026" not in rows[0]:
        raise ValueError("Expected retired model row missing")
    lines = [line.strip() for line in skill.splitlines() if line.startswith("| Claude |")]
    if len(lines) != 1 or MODEL not in lines[0] or "https://api.anthropic.com/v1" not in lines[0]:
        raise ValueError("Expected provider recommendation missing")
    choice = "Ask for their model preference" in skill
    if not choice:
        raise ValueError("Expected model-choice instruction missing")
    print(
        json.dumps(
            {
                "recommended_model": MODEL,
                "anthropic_api_status": "retired",
                "anthropic_table_retirement_date": "June 15, 2026",
                "skill_also_requests_model_preference": choice,
                "model_requests_executed": False,
                "agent_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
