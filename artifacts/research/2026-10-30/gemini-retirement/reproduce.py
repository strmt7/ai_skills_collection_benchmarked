"""Compare a retired Gemini model reference in source-bound skill revisions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

MODEL = "gemini-2.0-flash"
ENDPOINT = "models/gemini-2.0-flash:generateContent"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data, usedforsecurity=False).hexdigest()


def measure(path: Path, expected_sha256: str, expected_blob: str | None = None) -> dict[str, object]:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError(f"Source SHA-256 mismatch: {path.name}")
    if expected_blob is not None and git_blob(data) != expected_blob:
        raise ValueError(f"Git blob mismatch: {path.name}")
    text = data.decode("utf-8")
    return {
        "model_mentions": text.count(MODEL),
        "hardcoded_api_calls": text.count(ENDPOINT),
        "latest_available_mentions": text.lower().count("latest available"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--current-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = []
    for item in manifest["skills"]:
        result.append(
            {
                "name": item["name"],
                "skill_id": item["skill_id"],
                "pinned": measure(args.root / item["mirror_path"], item["mirror_sha256"]),
                "current": measure(
                    args.current_dir / f"{item['name']}.md", item["current_sha256"], item["current_git_blob_sha"]
                ),
            }
        )
    print(
        json.dumps(
            {
                "pinned_commit": manifest["pinned_commit"],
                "current_commit": manifest["observed_current_commit"],
                "skill_count": len(result),
                "skills": result,
                "api_calls_executed": False,
                "agent_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
