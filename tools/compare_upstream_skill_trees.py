"""Compare locked skill paths to immutable upstream Git trees without updating mirrors."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import quote

SHA = re.compile(r"[0-9a-f]{40}\Z")


def valid_sha(value: Any) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def parse_tree(
    payload: dict[str, Any], expected: str, *, recursive: bool
) -> tuple[bool, dict[str, tuple[str, str, str]]]:
    """Verify tree identity and entries; a truncated response is not complete evidence."""
    if not isinstance(payload, dict) or payload.get("sha") != expected or type(payload.get("truncated")) is not bool:
        raise ValueError("Git tree identity or truncation flag is invalid")
    items = payload.get("tree")
    if not isinstance(items, list):
        raise TypeError("Git tree has no entry array")
    entries = {}
    for item in items:
        if not isinstance(item, dict):
            raise TypeError("Invalid Git tree entry")
        path, mode, kind, sha = (item.get(key) for key in ("path", "mode", "type", "sha"))
        if (
            not isinstance(path, str)
            or not path
            or PurePosixPath(path).is_absolute()
            or PurePosixPath(path).as_posix() != path
            or any(part in {".", ".."} for part in path.split("/"))
            or (not recursive and "/" in path)
            or kind not in {"blob", "tree", "commit"}
            or mode not in {"100644", "100755", "120000", "040000", "160000"}
            or (kind == "tree" and mode != "040000")
            or (kind == "commit" and mode != "160000")
            or (kind == "blob" and mode not in {"100644", "100755", "120000"})
            or not valid_sha(sha)
            or path in entries
        ):
            raise ValueError("Invalid, duplicate or non-canonical Git tree entry")
        entries[path] = (str(kind), str(mode), str(sha))
    return not payload["truncated"], entries


class Snapshot:
    """Read complete root trees, falling back to targeted nonrecursive traversal."""

    def __init__(self, repo: str, tree_sha: str, fetch: Any):
        if not valid_sha(tree_sha):
            raise ValueError("Invalid root tree SHA")
        self.repo, self.root, self.fetch = repo, tree_sha, fetch
        self.cache: dict[tuple[str, bool], tuple[bool, dict[str, tuple[str, str, str]]]] = {}
        self.complete, self.root_entries = self.tree(tree_sha, True)

    def tree(self, sha: str, recursive: bool) -> tuple[bool, dict[str, tuple[str, str, str]]]:
        key = sha, recursive
        if key not in self.cache:
            endpoint = f"repos/{self.repo}/git/trees/{sha}" + ("?recursive=1" if recursive else "")
            self.cache[key] = parse_tree(self.fetch(endpoint), sha, recursive=recursive)
        return self.cache[key]

    def _walk(self, sha: str, prefix: str, ancestors: frozenset[str]) -> dict[str, tuple[str, str, str]]:
        if sha in ancestors:
            raise ValueError("Git tree traversal contains a cycle")
        complete, entries = self.tree(sha, False)
        if not complete:
            raise ValueError("Nonrecursive Git tree response is truncated")
        found = {}
        for name, value in entries.items():
            path = f"{prefix}/{name}" if prefix else name
            if value[0] == "tree":
                found.update(self._walk(value[2], path, ancestors | {sha}))
            else:
                found[path] = value
        return found

    def directory(self, directory: str) -> dict[str, tuple[str, str, str]]:
        prefix = "" if directory == "." else directory + "/"
        if self.complete:
            return {
                path[len(prefix) :]: value
                for path, value in self.root_entries.items()
                if path.startswith(prefix) and value[0] != "tree"
            }
        current = self.root
        if directory != ".":
            for component in directory.split("/"):
                complete, entries = self.tree(current, False)
                if not complete:
                    raise ValueError("Nonrecursive Git tree response is truncated")
                value = entries.get(component)
                if value is None or value[0] != "tree":
                    return {}
                current = value[2]
        complete, entries = self.tree(current, True)
        if complete:
            return {path: value for path, value in entries.items() if value[0] != "tree"}
        return self._walk(current, "", frozenset())

    def same_named_entrypoints(self, path: PurePosixPath) -> list[str] | None:
        """Find exact folder and entrypoint names only when the root tree is complete."""
        if not self.complete:
            return None
        return sorted(
            name
            for name, value in self.root_entries.items()
            if value[0] == "blob"
            and PurePosixPath(name).name == path.name
            and PurePosixPath(name).parent.name == path.parent.name
        )


def changed_paths(
    before: dict[str, tuple[str, str, str]], after: dict[str, tuple[str, str, str]]
) -> list[dict[str, Any]]:
    return [
        {"path": name, "pinned": before.get(name), "observed": after.get(name)}
        for name in sorted(before.keys() | after.keys())
        if before.get(name) != after.get(name)
    ]


def compare_skill(skill: dict[str, Any], pinned: Snapshot, observed: Snapshot) -> dict[str, Any]:
    source_path = skill["source_path"]
    path = PurePosixPath(source_path)
    if (
        path.is_absolute()
        or path.as_posix() != source_path
        or any(part in {".", ".."} for part in source_path.split("/"))
    ):
        raise ValueError("Invalid source skill path")
    directory = path.parent.as_posix()
    before, after = pinned.directory(directory), observed.directory(directory)
    filename = path.name
    if filename not in before or before[filename][0] != "blob":
        raise ValueError(f"Pinned entrypoint absent or not a blob: {source_path}")
    changes = changed_paths(before, after)
    entrypoint = (
        "missing_at_recorded_path"
        if filename not in after
        else "unchanged"
        if before[filename] == after[filename]
        else "changed"
    )
    candidate_paths = observed.same_named_entrypoints(path) if entrypoint == "missing_at_recorded_path" else []
    candidates = None
    if candidate_paths is not None:
        candidates = []
        for candidate_path in candidate_paths:
            candidate = PurePosixPath(candidate_path)
            candidate_files = observed.directory(candidate.parent.as_posix())
            candidates.append(
                {
                    "source_path": candidate_path,
                    "entrypoint_identical": before[filename] == candidate_files[candidate.name],
                    "observed_file_count": len(candidate_files),
                    "changed_paths": changed_paths(before, candidate_files),
                }
            )
    return {
        "skill_id": skill["id"],
        "source_path": source_path,
        "entrypoint": entrypoint,
        "directory_changed": bool(changes),
        "pinned_file_count": len(before),
        "observed_file_count": len(after),
        "changed_paths": changes,
        "same_named_candidates": candidates,
    }


class GitHubApiError(RuntimeError):
    def __init__(self, endpoint: str, capture: str, status: int | None):
        super().__init__(f"GitHub API failed for {endpoint}; retained capture {capture}")
        self.status = status


class Capture:
    """Retain native GitHub API response bytes and a digest for every request."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.cache: dict[str, Any] = {}
        self.receipts: list[dict[str, Any]] = []

    def __call__(self, endpoint: str) -> Any:
        if endpoint not in self.cache:
            try:
                run = subprocess.run(
                    ["gh", "api", endpoint],
                    capture_output=True,
                    timeout=90,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                self.record(endpoint, exc.stdout or b"", exc.stderr or b"", None)
                raise
            self.record(endpoint, run.stdout, run.stderr, run.returncode)
        return self.cache[endpoint]

    def record(self, endpoint: str, stdout: bytes, stderr: bytes, exit_code: int | None) -> None:
        stem = f"{len(self.receipts):04d}"
        (self.directory / f"{stem}.stdout").write_bytes(stdout)
        (self.directory / f"{stem}.stderr").write_bytes(stderr)
        self.receipts.append(
            {
                "endpoint": endpoint,
                "exit_code": exit_code,
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
                "capture": stem,
            }
        )
        if exit_code is None:
            raise TimeoutError(f"GitHub API timed out for {endpoint}; retained capture {stem}")
        if exit_code:
            match = re.search(rb"HTTP (\d{3})", stderr)
            raise GitHubApiError(endpoint, stem, int(match.group(1)) if match else None)
        self.cache[endpoint] = json.loads(stdout)


class ReplayCapture(Capture):
    """Replay retained responses only after verifying each native stream digest."""

    def __init__(self, directory: Path, source: Path, manifest: dict[str, Any]):
        super().__init__(directory)
        self.source = source
        captures = manifest["captures"]
        if not isinstance(captures, list) or any(not isinstance(item, dict) for item in captures):
            raise ValueError("Replay capture manifest is invalid")
        self.captured = {item["endpoint"]: item for item in captures}
        if len(self.captured) != len(captures):
            raise ValueError("Replay capture manifest contains duplicate endpoints")

    def __call__(self, endpoint: str) -> Any:
        if endpoint not in self.cache:
            item = self.captured[endpoint]
            stem = item["capture"]
            if (
                not isinstance(stem, str)
                or re.fullmatch(r"\d{4}", stem) is None
                or not (item["exit_code"] is None or type(item["exit_code"]) is int)
            ):
                raise ValueError("Replay capture identity is invalid")
            stdout = (self.source / f"{stem}.stdout").read_bytes()
            stderr = (self.source / f"{stem}.stderr").read_bytes()
            if (
                hashlib.sha256(stdout).hexdigest() != item["stdout_sha256"]
                or hashlib.sha256(stderr).hexdigest() != item["stderr_sha256"]
            ):
                raise ValueError("Replay capture digest differs")
            self.record(endpoint, stdout, stderr, item["exit_code"])
        return self.cache[endpoint]


def commit_tree(repo: str, commit: str, fetch: Any) -> str:
    if not valid_sha(commit):
        raise ValueError("Invalid commit SHA")
    obj = fetch(f"repos/{repo}/git/commits/{commit}")
    if obj.get("sha") != commit or not valid_sha(obj.get("tree", {}).get("sha")):
        raise ValueError("Git commit response does not match the requested commit")
    return obj["tree"]["sha"]


def inspect(repo: str, source: dict[str, Any], selected: list[dict[str, Any]], fetch: Any) -> dict[str, Any]:
    meta = fetch(f"repos/{repo}")
    canonical, branch = meta["full_name"], meta["default_branch"]
    if not isinstance(canonical, str) or canonical.lower() != repo.lower() or not isinstance(branch, str) or not branch:
        raise ValueError("Repository identity or default branch differs")
    head = fetch(f"repos/{repo}/commits/{quote(branch, safe='')}")["sha"]
    pinned = source["commit_sha"]
    left = Snapshot(repo, commit_tree(repo, pinned, fetch), fetch)
    right = Snapshot(repo, commit_tree(repo, head, fetch), fetch)
    rows = [compare_skill(skill, left, right) for skill in selected]
    try:
        release = fetch(f"repos/{repo}/releases/latest")
    except GitHubApiError as exc:
        if exc.status != 404:
            raise
        release = None
    release_result = None
    if release is not None:
        tag = release["tag_name"]
        if (
            not isinstance(tag, str)
            or not tag
            or release.get("draft") is not False
            or release.get("prerelease") is not False
        ):
            raise ValueError("Latest-release metadata is not a published stable release")
        release_commit = fetch(f"repos/{repo}/commits/{quote(tag, safe='')}")["sha"]
        release_snapshot = Snapshot(repo, commit_tree(repo, release_commit, fetch), fetch)
        release_rows = [compare_skill(skill, left, release_snapshot) for skill in selected]
        release_result = {
            "tag": tag,
            "commit": release_commit,
            "tree": release_snapshot.root,
            "recursive_complete": release_snapshot.complete,
            "entrypoints_changed": sum(row["entrypoint"] == "changed" for row in release_rows),
            "entrypoints_missing_at_recorded_path": sum(
                row["entrypoint"] == "missing_at_recorded_path" for row in release_rows
            ),
            "directories_changed": sum(row["directory_changed"] for row in release_rows),
            "skills": release_rows,
        }
    return {
        "repo": repo,
        "default_branch": branch,
        "pinned_commit": pinned,
        "observed_head": head,
        "pinned_tree": left.root,
        "observed_tree": right.root,
        "pinned_recursive_complete": left.complete,
        "observed_recursive_complete": right.complete,
        "selected_skill_count": len(rows),
        "entrypoints_changed": sum(row["entrypoint"] == "changed" for row in rows),
        "entrypoints_missing_at_recorded_path": sum(row["entrypoint"] == "missing_at_recorded_path" for row in rows),
        "directories_changed": sum(row["directory_changed"] for row in rows),
        "skills": rows,
        "latest_release": release_result,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument(
        "--selection",
        type=Path,
        required=True,
        help="JSON object mapping repository names to selected skill IDs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory for raw API captures and summary",
    )
    parser.add_argument("--observed-at-utc", required=True)
    parser.add_argument(
        "--replay",
        type=Path,
        help="Replay a previous capture directory without network access",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    stamp = datetime.fromisoformat(args.observed_at_utc)
    if stamp.tzinfo is None or stamp.utcoffset() != UTC.utcoffset(stamp):
        raise ValueError("Observation time must be an explicit UTC timestamp")
    lock_bytes, selection_bytes = (
        args.source_lock.read_bytes(),
        args.selection.read_bytes(),
    )
    sources = {source["repo"].lower(): source for source in json.loads(lock_bytes)["sources"]}
    selection = json.loads(selection_bytes)
    if not isinstance(selection, dict) or not selection:
        raise ValueError("Selection must map at least one repository to skill IDs")
    if len({repo.lower() for repo in selection}) != len(selection):
        raise ValueError("Selection contains a duplicate repository identity")
    replay_manifest = None
    if args.replay:
        replay_manifest = json.loads((args.replay / "summary.json").read_bytes())
        if (
            replay_manifest.get("schema_version") != 1
            or replay_manifest.get("source_lock_sha256") != hashlib.sha256(lock_bytes).hexdigest()
            or replay_manifest.get("selection_sha256") != hashlib.sha256(selection_bytes).hexdigest()
            or replay_manifest.get("observed_at_utc") != args.observed_at_utc
        ):
            raise ValueError("Replay source, selection or observation time differs")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    capture = (
        ReplayCapture(output, args.replay, replay_manifest) if args.replay and replay_manifest else Capture(output)
    )
    results = []
    for repo, ids in selection.items():
        try:
            source = sources[repo.lower()]
            available = {skill["id"]: skill for skill in source["skills"]}
            if (
                not isinstance(ids, list)
                or not ids
                or any(not isinstance(item, str) for item in ids)
                or len(set(ids)) != len(ids)
            ):
                raise ValueError("Selection must contain distinct skill IDs")
            selected = [available[item] for item in ids]
            results.append(
                {
                    "status": "complete",
                    **inspect(source["repo"], source, selected, capture),
                }
            )
        except (
            KeyError,
            ValueError,
            TypeError,
            RuntimeError,
            OSError,
            subprocess.TimeoutExpired,
        ) as exc:
            results.append({"repo": repo, "status": "error", "error": str(exc)})
    summary = {
        "schema_version": 1,
        "observed_at_utc": args.observed_at_utc,
        "source_lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "selection_sha256": hashlib.sha256(selection_bytes).hexdigest(),
        "algorithm_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Pinned selected skill directories compared with captured default-branch heads and latest GitHub releases; same-named paths are candidates only, not confirmed relocations. This is not an inventory of newly added skills, a quality review, or an agent-performance test.",
        "results": results,
        "captures": capture.receipts,
    }
    (output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "ok": all(row["status"] == "complete" for row in results),
                "repositories": len(results),
                "complete": sum(row["status"] == "complete" for row in results),
                "errors": sum(row["status"] != "complete" for row in results),
            }
        )
    )
    return int(any(row["status"] != "complete" for row in results))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run(args)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
