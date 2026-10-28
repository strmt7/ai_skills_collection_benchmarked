#!/usr/bin/env python3
"""Compare a locked skill selection against two verified upstream Git trees."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

MAX_INPUT_BYTES = 64 * 1024 * 1024
MODES = {"tree": {"040000"}, "blob": {"100644", "100755", "120000"}, "commit": {"160000"}}
OBJECT_ID = re.compile(r"[0-9a-f]{40}\Z")


def read_object(path: Path) -> tuple[dict[str, Any], str]:
    """Read bounded JSON without silently accepting duplicate keys or nonfinite numbers."""
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds the byte limit: {path}")
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as stream:
            raw = stream.read(MAX_INPUT_BYTES + 1)
    else:
        raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds the byte limit: {path}")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject(value: str) -> None:
        raise ValueError(f"Nonfinite JSON number: {value}")

    value = json.loads(raw, object_pairs_hook=unique, parse_constant=reject)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value, hashlib.sha256(raw).hexdigest()


def git_id(value: Any) -> str:
    if not isinstance(value, str) or not OBJECT_ID.fullmatch(value):
        raise ValueError("Expected a lowercase 40-character Git object ID")
    return value


def git_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\0" in value or "\\" in value:
        raise ValueError("Invalid Git tree path")
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise ValueError("Noncanonical Git tree path")
    return value


def verify_tree(tree: dict[str, Any], expected_root: str) -> dict[str, dict[str, str]]:
    """Reconstruct and verify every tree object, including omitted or altered subtrees."""
    expected_root = git_id(expected_root)
    if tree.get("sha") != expected_root or tree.get("truncated") is not False or not isinstance(tree.get("tree"), list):
        raise ValueError("Git tree is truncated, malformed, or bound to a different root")
    entries: dict[str, dict[str, str]] = {}
    children: dict[str, list[dict[str, str]]] = {"": []}
    for raw in tree["tree"]:
        if not isinstance(raw, dict):
            raise ValueError("Git tree entry must be an object")
        path, kind, mode, sha = git_path(raw.get("path")), raw.get("type"), raw.get("mode"), git_id(raw.get("sha"))
        if not isinstance(kind, str) or not isinstance(mode, str) or kind not in MODES or mode not in MODES[kind]:
            raise ValueError(f"Unsupported Git object type or mode: {path}")
        if path in entries:
            raise ValueError(f"Duplicate Git tree path: {path}")
        entry = {"path": path, "type": kind, "mode": mode, "sha": sha}
        entries[path] = entry
        if kind == "tree":
            children[path] = []
    for path, entry in entries.items():
        parent = str(PurePosixPath(path).parent)
        parent = "" if parent == "." else parent
        if parent not in children:
            raise ValueError(f"Git tree is missing an ancestor: {path}")
        children[parent].append(entry)
    for directory in sorted(children, key=lambda value: value.count("/") + bool(value), reverse=True):

        def sort_key(entry: dict[str, str]) -> bytes:
            name = PurePosixPath(entry["path"]).name.encode("utf-8")
            return name + (b"/" if entry["type"] == "tree" else b"")

        parts = []
        for entry in sorted(children[directory], key=sort_key):
            name = PurePosixPath(entry["path"]).name.encode("utf-8")
            mode = format(int(entry["mode"], 8), "o").encode("ascii")
            parts.append(mode + b" " + name + b"\0" + bytes.fromhex(entry["sha"]))
        payload = b"".join(parts)
        digest = hashlib.sha1(b"tree " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()
        expected = expected_root if not directory else entries[directory]["sha"]
        if digest != expected:
            raise ValueError(f"Git tree object does not match its identity: {directory or '/'}")
    return entries


def commit_tree(commit: dict[str, Any]) -> tuple[str, str]:
    tree = commit.get("tree")
    if not isinstance(tree, dict):
        raise ValueError("Git commit response has no tree")
    return git_id(commit.get("sha")), git_id(tree.get("sha"))


def resources(entries: dict[str, dict[str, str]], prefix: str) -> dict[str, dict[str, str]]:
    return {
        name[len(prefix) :]: {key: row[key] for key in ("type", "mode", "sha")}
        for name, row in entries.items()
        if name.startswith(prefix) and row["type"] != "tree"
    }


def compare(
    lock: dict[str, Any],
    repo: str,
    old_commit: dict[str, Any],
    old_tree: dict[str, Any],
    new_commit: dict[str, Any],
    new_tree: dict[str, Any],
    input_sha256: dict[str, str],
) -> dict[str, Any]:
    if (
        not isinstance(repo, str)
        or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo)
        or any(part in {".", ".."} for part in repo.split("/"))
    ):
        raise ValueError("Expected an owner/repository identity")
    sources = lock.get("sources")
    if (
        type(lock.get("lock_version")) is not int
        or lock["lock_version"] != 1
        or lock.get("hash_algorithm") != "sha256"
        or not isinstance(sources, list)
    ):
        raise ValueError("Unsupported source lock or missing sources")
    selected = [source for source in sources if isinstance(source, dict) and source.get("repo") == repo]
    if len(selected) != 1:
        raise ValueError("Expected exactly one locked source for the selected repository")
    source = selected[0]
    old_id, old_root = commit_tree(old_commit)
    new_id, new_root = commit_tree(new_commit)
    if source.get("commit_sha") != old_id:
        raise ValueError("Old commit does not match the selected source lock")
    old, new = verify_tree(old_tree, old_root), verify_tree(new_tree, new_root)
    skills = source.get("skills")
    if (
        not isinstance(skills, list)
        or not skills
        or type(source.get("skill_count")) is not int
        or source["skill_count"] != len(skills)
    ):
        raise ValueError("Source lock skill inventory is inconsistent")
    records: list[dict[str, Any]] = []
    seen_ids, seen_paths = set(), set()
    for skill in skills:
        if not isinstance(skill, dict) or not isinstance(skill.get("id"), str) or not skill["id"]:
            raise ValueError("Malformed locked skill")
        skill_id, path = skill["id"], git_path(skill.get("source_path"))
        if PurePosixPath(path).name != "SKILL.md" or skill_id in seen_ids or path in seen_paths:
            raise ValueError("Locked skill identities and entrypoints must be unique")
        seen_ids.add(skill_id)
        seen_paths.add(path)
        if path not in old or old[path]["type"] != "blob" or old[path]["mode"] not in {"100644", "100755"}:
            raise ValueError(f"Locked entrypoint is absent from its source tree: {path}")
        parent = PurePosixPath(path).parent
        prefix = "" if parent == PurePosixPath(".") else str(parent) + "/"

        before, after = resources(old, prefix), resources(new, prefix)
        names = sorted(before.keys() | after.keys())
        changes = [
            {"path": name, "before": before.get(name), "after": after.get(name)}
            for name in names
            if before.get(name) != after.get(name)
        ]
        records.append(
            {
                "skill_id": skill_id,
                "source_path": path,
                "old_resource_count": len(before),
                "new_resource_count": len(after),
                "new_entrypoint_present": path in new
                and new[path]["type"] == "blob"
                and new[path]["mode"] in {"100644", "100755"},
                "changed": bool(changes),
                "changes": changes,
            }
        )
    records.sort(key=lambda item: item["skill_id"])
    return {
        "schema_version": 1,
        "measurement_kind": "raw_upstream_git_tree_comparison",
        "repository": repo,
        "old_commit": old_id,
        "old_tree": old_root,
        "new_commit": new_id,
        "new_tree": new_root,
        "input_sha256": input_sha256,
        "skill_count": len(records),
        "changed_skills": sum(record["changed"] for record in records),
        "missing_new_entrypoints": sum(not record["new_entrypoint_present"] for record in records),
        "limitations": [
            "Commit-to-tree bindings rely on authentic supplied GitHub API responses; commit signatures are not verified.",
            "Only SHA-1 Git object IDs are supported; matching object IDs do not rule out hash collisions.",
            "Raw directory entries can include nested skills, symlinks or submodules; this is not mirror admission or a runtime audit.",
            "A changed Git object is not proof of an improvement, regression, security fix, or agent performance.",
        ],
        "skills": records,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    for name in ("old-commit", "old-tree", "new-commit", "new-tree"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = {name: getattr(args, name) for name in ("lock", "old_commit", "old_tree", "new_commit", "new_tree")}
        if any(args.output.resolve() == path.resolve() for path in paths.values()) or args.output.is_symlink():
            raise ValueError("Output must not replace an input or a symbolic link")
        inputs = {name: read_object(path) for name, path in paths.items()}
        report = compare(
            inputs["lock"][0],
            args.repo,
            inputs["old_commit"][0],
            inputs["old_tree"][0],
            inputs["new_commit"][0],
            inputs["new_tree"][0],
            {
                **{name: value[1] for name, value in inputs.items()},
                "tool": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
        )
        expected = (json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if args.check:
            if args.output.stat().st_size != len(expected) or args.output.read_bytes() != expected:
                raise ValueError("Recorded comparison differs from verified inputs")
        else:
            if args.output.exists():
                raise ValueError("Comparison output already exists")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("xb") as destination:
                destination.write(expected)
        print(
            json.dumps(
                {
                    "ok": True,
                    "skills": report["skill_count"],
                    "changed": report["changed_skills"],
                    "missing_entrypoints": report["missing_new_entrypoints"],
                }
            )
        )
        return 0
    except (OSError, EOFError, UnicodeError, ValueError, TypeError, KeyError, RecursionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
