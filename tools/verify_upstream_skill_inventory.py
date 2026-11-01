"""Independently reconcile one retained inventory against complete native Git trees."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(capture: Path, selection_path: Path, source_lock_path: Path) -> dict[str, Any]:
    selection_bytes = selection_path.read_bytes()
    lock_bytes = source_lock_path.read_bytes()
    selection = json.loads(selection_bytes)
    lock = json.loads(lock_bytes)
    summary_bytes = (capture / "summary.json").read_bytes()
    summary = json.loads(summary_bytes)
    if summary["selection_sha256"] != digest(selection_bytes) or summary["source_lock_sha256"] != digest(lock_bytes):
        raise ValueError("Selection or source lock digest differs")
    locked = {item["repo"]: {skill["id"]: skill["source_path"] for skill in item["skills"]} for item in lock["sources"]}
    pins = {item["repo"]: item["commit_sha"] for item in lock["sources"]}
    raw: dict[str, Any] = {}
    receipts = {}
    used_stems = set()
    for receipt in summary["captures"]:
        name = receipt["capture"]
        if not isinstance(name, str) or len(name) != 4 or not name.isascii() or not name.isdecimal():
            raise ValueError("Invalid capture identity")
        if name in used_stems:
            raise ValueError("Duplicate capture identity")
        used_stems.add(name)
        stdout = (capture / f"{name}.stdout").read_bytes()
        stderr = (capture / f"{name}.stderr").read_bytes()
        if digest(stdout) != receipt["stdout_sha256"] or digest(stderr) != receipt["stderr_sha256"]:
            raise ValueError("Captured stream digest mismatch")
        if receipt["endpoint"] in receipts:
            raise ValueError("Duplicate captured endpoint")
        receipts[receipt["endpoint"]] = (receipt, stderr)
        if receipt["exit_code"] == 0:
            raw[receipt["endpoint"]] = json.loads(stdout)

    def files(repo: str, tree_sha: str) -> dict[str, list[str]]:
        tree = raw[f"repos/{repo}/git/trees/{tree_sha}?recursive=1"]
        if tree["sha"] != tree_sha or tree["truncated"] is not False:
            raise ValueError("Independent comparison requires a complete root tree")
        values = [item for item in tree["tree"] if item["type"] != "tree"]
        result = {item["path"]: [item["type"], item["mode"], item["sha"]] for item in values}
        if len(result) != len(values):
            raise ValueError("Duplicate Git tree paths")
        return result

    def directory(tree: dict[str, list[str]], path: str) -> dict[str, list[str]]:
        prefix = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
        return {name[len(prefix) :]: value for name, value in tree.items() if name.startswith(prefix)}

    comparisons = 0
    candidate_count = 0
    if {repo["repo"] for repo in summary["results"]} != set(selection):
        raise ValueError("Repository selection is incomplete")
    for repo in summary["results"]:
        name = repo["repo"]
        if (
            repo["status"] != "complete"
            or repo["pinned_commit"] != pins[name]
            or repo["selected_skill_count"] != len(selection[name])
            or len(repo["skills"]) != len(selection[name])
            or {item["skill_id"] for item in repo["skills"]} != set(selection[name])
        ):
            raise ValueError("Repository skill selection is incomplete")
        metadata = raw[f"repos/{name}"]
        branch = metadata["default_branch"]
        head = raw[f"repos/{name}/commits/{quote(branch, safe='')}"]["sha"]
        if metadata["full_name"].lower() != name.lower() or head != repo["observed_head"]:
            raise ValueError("Default branch observation differs")
        pinned = files(name, repo["pinned_tree"])
        pinned_commit = raw[f"repos/{name}/git/commits/{repo['pinned_commit']}"]
        if pinned_commit["sha"] != repo["pinned_commit"] or pinned_commit["tree"]["sha"] != repo["pinned_tree"]:
            raise ValueError("Pinned commit-to-tree mismatch")
        states = [(repo["observed_head"], repo["observed_tree"], repo["skills"], repo)]
        if repo["latest_release"] is not None:
            release = repo["latest_release"]
            release_meta = raw[f"repos/{name}/releases/latest"]
            tag = release_meta["tag_name"]
            resolved = raw[f"repos/{name}/commits/{quote(tag, safe='')}"]["sha"]
            if (
                tag != release["tag"]
                or resolved != release["commit"]
                or release_meta["draft"] is not False
                or release_meta["prerelease"] is not False
            ):
                raise ValueError("Latest-release observation differs")
            states.append((release["commit"], release["tree"], release["skills"], release))
        else:
            receipt, stderr = receipts[f"repos/{name}/releases/latest"]
            if not receipt["exit_code"] or b"HTTP 404" not in stderr:
                raise ValueError("Missing-release observation is not an HTTP 404")
        for commit, tree_sha, rows, recorded in states:
            if len(rows) != len(selection[name]) or {row["skill_id"] for row in rows} != set(selection[name]):
                raise ValueError("Comparison skill selection is incomplete")
            commit_obj = raw[f"repos/{name}/git/commits/{commit}"]
            if commit_obj["sha"] != commit or commit_obj["tree"]["sha"] != tree_sha:
                raise ValueError("Commit-to-tree mismatch")
            observed = files(name, tree_sha)
            for row in rows:
                path = row["source_path"]
                if locked[name][row["skill_id"]] != path:
                    raise ValueError("Skill path differs from the source lock")
                filename = path.rsplit("/", 1)[-1]
                before, after = directory(pinned, path), directory(observed, path)
                expected = [
                    {"path": n, "pinned": before.get(n), "observed": after.get(n)}
                    for n in sorted(before.keys() | after.keys())
                    if before.get(n) != after.get(n)
                ]
                status = (
                    "missing_at_recorded_path"
                    if filename not in after
                    else "unchanged"
                    if before[filename] == after[filename]
                    else "changed"
                )
                if (
                    row["changed_paths"] != expected
                    or row["entrypoint"] != status
                    or row["directory_changed"] != bool(expected)
                    or row["pinned_file_count"] != len(before)
                    or row["observed_file_count"] != len(after)
                ):
                    raise ValueError(f"Tree comparison differs for {name}/{path}")
                if status == "missing_at_recorded_path":
                    parent = path.split("/")[-2] if "/" in path else ""
                    matches = sorted(
                        n
                        for n, v in observed.items()
                        if n.endswith("/" + filename) and n.split("/")[-2] == parent and v[0] == "blob"
                    )
                    if [item["source_path"] for item in row["same_named_candidates"]] != matches:
                        raise ValueError(f"Candidate path mismatch for {name}/{path}")
                    for candidate in row["same_named_candidates"]:
                        found = directory(observed, candidate["source_path"])
                        expected = [
                            {
                                "path": n,
                                "pinned": before.get(n),
                                "observed": found.get(n),
                            }
                            for n in sorted(before.keys() | found.keys())
                            if before.get(n) != found.get(n)
                        ]
                        if (
                            candidate["changed_paths"] != expected
                            or candidate["entrypoint_identical"] != (before[filename] == found[filename])
                            or candidate["observed_file_count"] != len(found)
                        ):
                            raise ValueError(f"Candidate content mismatch for {name}/{path}")
                        candidate_count += 1
                comparisons += 1
            if (
                recorded["entrypoints_changed"] != sum(row["entrypoint"] == "changed" for row in rows)
                or recorded["entrypoints_missing_at_recorded_path"]
                != sum(row["entrypoint"] == "missing_at_recorded_path" for row in rows)
                or recorded["directories_changed"] != sum(row["directory_changed"] for row in rows)
            ):
                raise ValueError("Aggregate counts differ from individual skills")
    return {
        "ok": True,
        "summary_sha256": digest(summary_bytes),
        "repository_count": len(summary["results"]),
        "skill_tree_comparisons": comparisons,
        "candidate_directories_checked": candidate_count,
        "native_streams_checked": len(summary["captures"]) * 2,
        "scope": "Complete root tree reconciliation only; source quality, relocations and agent effectiveness were not verified.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify(args.capture, args.selection, args.source_lock)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
