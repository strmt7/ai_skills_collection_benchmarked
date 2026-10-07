#!/usr/bin/env python3
"""Build a bounded offline text review; it does not grade or execute agent output."""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
from typing import Any

MAX_INPUT_BYTES = 2 * 1024 * 1024
FIELDS = {"id", "prompt", "output_text"}
SCRIPT = """document.querySelector('button').addEventListener('click', () => {
  const reviews = [...document.querySelectorAll('section')].map(section => ({
    run_id: section.dataset.runId,
    reviewed: section.querySelector('select').value !== 'pending',
    verdict: section.querySelector('select').value,
    feedback: section.querySelector('textarea').value
  }));
  const complete = reviews.every(review => review.reviewed);
  const blob = new Blob([JSON.stringify({reviews, status: complete ? 'complete' : 'in_progress'}, null, 2)],
    {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = 'feedback.json'; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  document.querySelector('#status').textContent = complete ? 'All runs reviewed; feedback exported.' : 'Unreviewed runs remain; partial feedback exported.';
});"""
STYLE = "body{font:16px system-ui;margin:2rem;max-width:70rem}section{border-top:1px solid #888;padding:1rem 0}pre{white-space:pre-wrap;overflow-wrap:anywhere}textarea{display:block;width:100%;min-height:6rem}select,button{font:inherit;margin:.5rem 0}"


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def read_runs(path: Path) -> list[dict[str, str]]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("review input exceeds 2 MiB")
    runs = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if not isinstance(runs, list) or not 1 <= len(runs) <= 100:
        raise ValueError("review requires 1 to 100 runs")
    ids = set()
    for run in runs:
        if not isinstance(run, dict) or run.keys() != FIELDS:
            raise ValueError("each run requires exactly id, prompt and output_text")
        if not all(isinstance(value, str) and len(value) <= 65536 for value in run.values()):
            raise ValueError("run fields must be strings of at most 65536 characters")
        if not run["id"].strip() or len(run["id"]) > 128 or run["id"] in ids:
            raise ValueError("run identifiers must be nonempty, unique and at most 128 characters")
        ids.add(run["id"])
    return runs


def content_hash(value: str) -> str:
    return base64.b64encode(hashlib.sha256(value.encode("utf-8")).digest()).decode("ascii")


def render(runs: list[dict[str, str]]) -> str:
    policy = f"default-src 'none'; script-src 'sha256-{content_hash(SCRIPT)}'; style-src 'sha256-{content_hash(STYLE)}'; base-uri 'none'; form-action 'none'"
    parts = [
        f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="{html.escape(policy, quote=True)}"><title>Skill output review</title><style>{STYLE}</style><h1>Skill output review</h1><p>Review each run explicitly. Outputs appear as text. Export saves your feedback locally.</p>'
    ]
    for index, run in enumerate(runs):
        parts.append(
            f'<section data-run-id="{html.escape(run["id"], quote=True)}"><h2>{html.escape(run["id"])}</h2><h3>Prompt</h3><pre>{html.escape(run["prompt"])}</pre><h3>Output</h3><pre>{html.escape(run["output_text"])}</pre><label for="verdict-{index}">Review verdict</label><select id="verdict-{index}"><option value="pending">Not reviewed</option><option value="acceptable">Acceptable</option><option value="needs_change">Needs changes</option></select><label for="feedback-{index}">Feedback</label><textarea id="feedback-{index}"></textarea></section>'
        )
    parts.append(
        f'<button type="button">Export feedback</button><p id="status" role="status"></p><script>{SCRIPT}</script></html>'
    )
    return "\n".join(parts) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 JSON array of id/prompt/output_text records")
    parser.add_argument("--output", required=True, type=Path, help="New standalone HTML file; never overwritten")
    parser.add_argument("--check", action="store_true", help="Check deterministic HTML freshness without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data = render(read_runs(args.input))
    if args.check:
        fresh = args.output.is_file() and args.output.read_bytes() == data.encode("utf-8")
        print(json.dumps({"fresh": fresh, "errors": [] if fresh else ["review is missing or differs from input"]}))
        return int(not fresh)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(data)
    print(f"Review written: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
