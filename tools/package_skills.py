"""Build a movable, integrity-checked installation of selected catalog skills."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Iterable, Iterator
from pathlib import Path, PurePosixPath
from typing import Any

import build_catalog
from _source_admission import require_admitted_source
from _trial_protocol import relative_path
from _trial_transcript import strict_json
from archive_catalog_source import git_bytes

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "package-manifest.json"
MAX_BYTES = 512 * 1024**2
MAX_FILES = 32768
GIT_MODES = {"100644", "100755"}
TOOL_SKILLS = ("caveman", "cocoindex-code-search", "crawl4ai-research")
RUNTIME_PATHS = (
    "dev.ps1",
    "pyproject.toml",
    "requirements-dev-lock.txt",
    "requirements-reports-lock.txt",
    "toolchains/bootstrap/ArchiveLayers.ps1",
    "toolchains/bootstrap/CompileSupervisor.ps1",
    "toolchains/bootstrap/FRAMEWORK-REFERENCES-LICENSE.txt",
    "toolchains/bootstrap/NativeCabinet.cs",
    "toolchains/bootstrap/NativeSupervisor.dll",
    "toolchains/bootstrap/OwnedProcess.cs",
    "toolchains/bootstrap/README.md",
    "toolchains/bootstrap/bootstrap.ps1",
    "toolchains/bootstrap/build_supervisor.ps1",
    "toolchains/bootstrap/codex.json",
    "toolchains/bootstrap/framework-reference-source.json",
    "toolchains/bootstrap/framework-references.json",
    "toolchains/bootstrap/manifest.json",
    "toolchains/bootstrap/powershell.json",
    "toolchains/bootstrap/requirements.txt",
    "toolchains/bootstrap/supervisor.json",
    "toolchains/bootstrap/uv.toml",
    "toolchains/cocoindex-code/CATALOG_BUILD_NOTICE.txt",
    "toolchains/cocoindex-code/LICENSE",
    "toolchains/cocoindex-code/README.md",
    "toolchains/cocoindex-code/model.json",
    "toolchains/cocoindex-code/requirements-bootstrap.txt",
    "toolchains/cocoindex-code/requirements-build.txt",
    "toolchains/cocoindex-code/requirements.txt",
    "toolchains/cocoindex-code/source.json",
    "toolchains/crawl4ai/CATALOG_BUILD_NOTICE.txt",
    "toolchains/crawl4ai/README.md",
    "toolchains/crawl4ai/browser.json",
    "toolchains/crawl4ai/requirements-bootstrap.txt",
    "toolchains/crawl4ai/requirements-build.txt",
    "toolchains/crawl4ai/requirements.txt",
    "toolchains/crawl4ai/source.json",
    "toolchains/crawl4ai/vendor/LICENSE",
    "toolchains/crawl4ai/vendor/crawl4ai_download_opener.py",
    *(f".agents/skills/{name}/SKILL.md" for name in TOOL_SKILLS),
    *(
        f"tools/{name}.py"
        for name in (
            "_agent_tool_runtime",
            "_bootstrap_archive",
            "_bootstrap_doctor",
            "_bootstrap_launch",
            "_catalog_publication",
            "_provider_launch",
            "_windows_owned_python",
            "check_crawl4ai_browser",
            "check_crawl4ai_contracts",
            "cocoindex_runtime",
            "cocoindex_tool",
            "crawl4ai_capture",
            "crawl4ai_runtime",
            "crawl4ai_tool",
            "prepare_cocoindex_source",
            "prepare_crawl4ai_source",
            "prepare_semantic_corpus",
            "search_semantic_corpus",
            "verify_cocoindex_wheel",
            "verify_crawl4ai_wheel",
        )
    ),
)

AGENT_POLICY = """# Mandatory agent tools

These requirements apply whenever an AI agent uses a skill in this package.

- Apply [Caveman](../.agents/skills/caveman/SKILL.md) to every task. Keep internal
  context concise and preserve exact technical meaning. Use clear public prose
  and report material failures and results.
- Use [CocoIndex Code](../.agents/skills/cocoindex-code-search/SKILL.md) before
  broad or conceptual repository searches. Bind the corpus to the repository
  you are working on, retain the native search result, and confirm relevant
  spans in current source. Use exact searches for known identifiers and paths.
- Use [Crawl4AI](../.agents/skills/crawl4ai-research/SKILL.md) to read web pages.
  Retain the native capture and its source, status, extracted text and digest.
  Use a reviewed isolated browser with bounded time and automation disclosed.
  Honor access denials. Exact API, package and archive bytes use their native
  transport.

Use tools without routine narration. If a required tool fails, preserve the
failure, restore the tool before dependent work, and continue only independent
work. Normal repository, user and access rules govern each task.

On Windows x64, the package launcher provisions missing tools in isolated
caches. Run commands from the package root. Select your working Git checkout
with CocoIndex Code's explicit root option. Keep your project files and search
index there. [CocoIndex Code setup](../toolchains/cocoindex-code/README.md#search-another-project)
and [Crawl4AI setup](../toolchains/crawl4ai/README.md#install-and-use).
"""

PACKAGE_README = """# Use the installed skills

Open this directory as a local workspace in a client that discovers skills in
`.agents/skills`. In another client, point its local skill setting or File tool
at a selected `SKILL.md` in that directory. Extract the archive into a new
location when moving to another workspace or computer. The package manifest
lists the installed catalog IDs and source commits.

Run the following from this directory on Windows x64 to prepare the required
providers. The launcher installs locked dependencies into owned caches.

```powershell
.\\dev.ps1 cocoindex check
.\\dev.ps1 crawl4ai check
```

Read the [agent-tool policy](docs/agent-tools.md) before using a skill. Follow
the linked source requirements when running its resources. The
[benchmark status](docs/benchmark-results.md) describes the evidence for the
included skills.
"""


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def snapshot(root: Path, revision: str, *paths: str) -> Iterator[tuple[str, str, str, bytes]]:
    """Read canonical Git blobs without checkout conversion or archive attributes."""
    expected: dict[str, tuple[str, str, int]] = {}
    for record in git_bytes(root, "ls-tree", "-r", "-l", "-z", revision, "--", *paths).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, oid, size_text = header.decode("ascii").split()
        path = relative_path(raw_path.decode("utf-8"))
        if mode not in GIT_MODES or kind != "blob" or path in expected:
            raise ValueError(f"Unsupported or duplicate Git resource: {path}")
        expected[path] = (mode, oid, int(size_text))
    if not expected or any(
        name not in expected and not any(path.startswith(name + "/") for path in expected) for name in paths
    ):
        raise ValueError("A required package input is missing at the catalog revision")
    if len(expected) > MAX_FILES or sum(row[2] for row in expected.values()) > MAX_BYTES:
        raise ValueError("Package input exceeds the resource budget")

    result = subprocess.run(
        ["git", "--no-optional-locks", "-c", "core.longpaths=true", "-C", str(root), "cat-file", "--batch"],
        input="".join(oid + "\n" for _, oid, _ in expected.values()).encode("ascii"),
        capture_output=True,
        check=True,
        timeout=60,
    )
    if result.stderr.strip():
        raise ValueError("Git reported diagnostics reading package objects")
    raw = result.stdout
    view = memoryview(raw)
    position = 0
    for name, (mode, oid, size) in expected.items():
        header = f"{oid} blob {size}\n".encode("ascii")
        start = position + len(header)
        stop = start + size
        if raw[position:start] != header or raw[stop : stop + 1] != b"\n":
            raise ValueError(f"Git blob stream differs from its tree record: {name}")
        data = bytes(view[start:stop])
        digest = hashlib.sha1(f"blob {size}\0".encode(), usedforsecurity=False)
        digest.update(data)
        if digest.hexdigest() != oid:
            raise ValueError(f"Git blob checksum differs from its tree record: {name}")
        yield name, mode, oid, data
        position = stop + 1
    if position != len(raw):
        raise ValueError("Git returned unexpected package object bytes")


def selected_rows(root: Path, revision: str, identifiers: list[str]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    catalog: list[dict[str, Any]] = json.loads(git_bytes(root, "show", f"{revision}:data/skills_catalog.json"))
    lock = json.loads(git_bytes(root, "show", f"{revision}:data/source_lock.json"))
    rows: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for identifier in sorted(set(identifiers)):
        matches = [row for row in catalog if row["id"] == identifier]
        if len(matches) != 1:
            raise ValueError(f"Expected one catalog entry for {identifier!r}")
        entry = matches[0]
        locked = [
            (source, skill) for source in lock["sources"] for skill in source["skills"] if skill["id"] == identifier
        ]
        if len(locked) != 1:
            raise ValueError(f"Expected one source lock for {identifier!r}")
        source, skill = locked[0]
        if any(
            entry[key] != skill[key] for key in ("source_path", "install_name", "skill_file_sha256", "skill_dir_sha256")
        ) or (entry["source_repo"], entry["commit_sha"], entry["selected_ref"]) != (
            source["repo"],
            source["commit_sha"],
            source["selected_ref"],
        ):
            raise ValueError(f"Catalog entry differs from its source lock: {identifier}")
        require_admitted_source(root, source["repo"], source["commit_sha"])
        rows.append((entry, source))
    if not rows:
        raise ValueError("Select at least one catalog skill")
    return rows


def put(archive: zipfile.ZipFile, name: str, data: bytes, mode: str) -> None:
    item = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    item.create_system = 3
    item.external_attr = int(mode, 8) << 16
    archive.writestr(item, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=6)


def portable_inventory(names: Iterable[str]) -> set[str]:
    """Check file and directory spelling on a case-insensitive installation."""
    members: set[str] = set()
    directories: dict[str, str] = {}
    file_keys: set[str] = set()
    for name in names:
        path = PurePosixPath(relative_path(name))
        folded = name.casefold()
        if folded in file_keys:
            raise ValueError(f"Package file paths collide: {name}")
        file_keys.add(folded)
        members.add(name)
        for parent in path.parents:
            if parent == PurePosixPath("."):
                continue
            spelling = parent.as_posix()
            if directories.setdefault(spelling.casefold(), spelling) != spelling:
                raise ValueError(f"Package directory paths collide: {name}")
    if file_keys & directories.keys():
        raise ValueError("Package paths overlap as files and directories")
    return members


def assemble(root: Path, revision: str, identifiers: list[str], output: Path) -> None:
    rows = selected_rows(root, revision, identifiers)
    files: dict[str, Any] = {}
    portable_paths: set[str] = set()
    skills: list[dict[str, Any]] = []
    results = ["# Benchmark status", ""]
    total_bytes = 0
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:

        def write(name: str, data: bytes, mode: str = "100644", *, git_blob: str | None = None) -> None:
            nonlocal total_bytes
            relative_path(name)
            normalized = name.casefold()
            if normalized in portable_paths:
                raise ValueError(f"Package paths collide on Windows: {name}")
            total_bytes += len(data)
            if total_bytes > MAX_BYTES or len(files) >= MAX_FILES:
                raise ValueError("Package exceeds the resource budget")
            portable_paths.add(normalized)
            put(archive, name, data, mode)
            files[name] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "mode": mode}
            if git_blob:
                files[name]["git_blob"] = git_blob

        for name, mode, oid, data in snapshot(root, revision, *RUNTIME_PATHS):
            write(name, data, mode, git_blob=oid)
        write("README.md", PACKAGE_README.encode())
        write("AGENTS.md", b"# Package instructions\n\nApply the [mandatory agent tools](docs/agent-tools.md).\n")
        write(".gitignore", b".venv/\n")
        write("docs/agent-tools.md", AGENT_POLICY.encode())

        notices: dict[str, str] = {}
        for entry, source in rows:
            alias = build_catalog.agent_ready_name(entry["install_name"])
            prefix = f".agents/skills/{alias}"
            mirror = relative_path(entry["mirrored_path"])
            if not mirror.startswith("included/skills/by-category/"):
                raise ValueError("The source mirror lies outside the catalog mirrors")
            mirror_target = f"sources/{alias}"
            expected_entrypoint = mirror_target + "/SKILL.md"
            for name, mode, oid, data in snapshot(root, revision, mirror):
                write(mirror_target + "/" + name.removeprefix(mirror + "/"), data, mode, git_blob=oid)
            if expected_entrypoint not in files:
                raise ValueError(f"Source mirror entrypoint is missing: {entry['id']}")
            payload = dict(entry, agent_ready_path=prefix + "/SKILL.md", mirrored_path=mirror_target)
            write(payload["agent_ready_path"], build_catalog.render_agent_ready_skill(payload).encode())
            details = {
                key: entry[key]
                for key in (
                    "id",
                    "source_repo",
                    "commit_sha",
                    "selected_ref",
                    "source_path",
                    "immutable_source_url",
                    "skill_file_sha256",
                    "skill_dir_sha256",
                )
            } | {"entrypoint": payload["agent_ready_path"], "source_entrypoint": expected_entrypoint}
            if notice := source.get("preserved_notice"):
                if notice["commit_sha"] != entry["commit_sha"] or not notice["path"].startswith(
                    "artifacts/source-notices/"
                ):
                    raise ValueError(f"Preserved notice binding differs: {entry['id']}")
                path = notice["path"]
                target = notices.get(path)
                if target is None:
                    [(name, mode, oid, data)] = list(snapshot(root, revision, path))
                    if name != path or hashlib.sha256(data).hexdigest() != notice["sha256"]:
                        raise ValueError(f"Preserved notice bytes differ: {entry['id']}")
                    target = "docs/source-notices/" + notice["sha256"] + "/" + PurePosixPath(path).name
                    if target not in files:
                        write(target, data, mode, git_blob=oid)
                    notices[path] = target
                details["source_notice"] = target
            skills.append(details)
            results.extend(
                [
                    f"## {entry['name']}",
                    "",
                    f"Catalog ID `{entry['id']}`",
                    f"Source revision `{entry['commit_sha']}`",
                    f"Recorded catalog status `{entry['benchmark_status']}`",
                    "",
                    f"[Pinned upstream instructions]({entry['immutable_source_url']})",
                    "",
                ]
            )

        results.extend(
            [
                "Catalog records describe the pinned skill. Package integrity and discovery are separate from",
                "runtime outcomes and comparative model effectiveness.",
                "",
            ]
        )
        write("docs/benchmark-results.md", "\n".join(results).encode())
        manifest = json_bytes({"schema_version": 1, "collection_commit": revision, "skills": skills, "files": files})
        put(archive, MANIFEST, manifest, "100644")


def verify(path: Path) -> dict[str, Any]:
    with path.open("rb") as raw, zipfile.ZipFile(raw) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES + 1 or sum(item.file_size for item in entries) > MAX_BYTES:
            raise ValueError("Package exceeds its resource budget")
        if any(
            item.is_dir() or item.create_system != 3 or item.external_attr >> 16 not in {0o100644, 0o100755}
            for item in entries
        ):
            raise ValueError("Package members must be regular files with portable modes")
        inventory = portable_inventory(item.filename for item in entries)
        manifest = strict_json(archive.read(MANIFEST).decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Package manifest must be a JSON object")
        files, skills, revision = (manifest.get(key) for key in ("files", "skills", "collection_commit"))
        if (
            type(manifest.get("schema_version")) is not int
            or manifest["schema_version"] != 1
            or not isinstance(files, dict)
            or inventory != set(files) | {MANIFEST}
            or MANIFEST in files
            or not isinstance(revision, str)
            or re.fullmatch(r"[0-9a-f]{40}", revision) is None
            or not isinstance(skills, list)
            or not skills
        ):
            raise ValueError("Package manifest differs from its expected schema or file inventory")
        required = {*RUNTIME_PATHS, "README.md", "AGENTS.md", "docs/agent-tools.md", "docs/benchmark-results.md"}
        if required - files.keys():
            raise ValueError("The package is missing a required runtime or policy file")
        identities = set()
        for skill in skills:
            identifier = skill["id"]
            entry = PurePosixPath(relative_path(skill["entrypoint"]))
            mirror = PurePosixPath("sources", entry.parent.name, "SKILL.md")
            if (
                not isinstance(identifier, str)
                or not identifier
                or identifier in identities
                or entry.as_posix() not in inventory
                or mirror.as_posix() not in inventory
                or entry.name != "SKILL.md"
                or entry.parent.parent.as_posix() != ".agents/skills"
                or entry.parent.name in TOOL_SKILLS
                or len(entry.parent.name) > 64
                or build_catalog.agent_ready_name(entry.parent.name) != entry.parent.name
                or skill["source_entrypoint"] != mirror.as_posix()
                or ("source_notice" in skill and skill["source_notice"] not in inventory)
            ):
                raise ValueError("A packaged skill has an inconsistent source or entrypoint")
            identities.add(identifier)
        for name, row in files.items():
            member = archive.getinfo(name)
            mode = member.external_attr >> 16
            if row["mode"] not in GIT_MODES or mode != int(row["mode"], 8) or member.file_size != row["bytes"]:
                raise ValueError(f"Package file metadata differs: {name}")
            sha256 = hashlib.sha256()
            with archive.open(member) as source:
                while block := source.read(1024 * 1024):
                    sha256.update(block)
            if sha256.hexdigest() != row["sha256"]:
                raise ValueError(f"Package file digest differs: {name}")
        raw.seek(0)
        digest = hashlib.file_digest(raw, "sha256").hexdigest()
        return {"collection_commit": revision, "skills": len(skills), "files": len(files), "sha256": digest}


def export(root: Path, identifiers: list[str], output: Path) -> dict[str, Any]:
    if output.suffix.lower() != ".zip" or output.is_symlink() or output.exists():
        raise ValueError("Choose a new .zip output file")
    revision = git_bytes(root, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("An immutable collection revision is required")
    with tempfile.TemporaryDirectory(prefix=".skill-package-", dir=output.parent) as scratch:
        package = Path(scratch) / "package.zip"
        assemble(root, revision, identifiers, package)
        report = verify(package)
        # Windows rename refuses an existing destination. POSIX link provides
        # the same atomic, no-clobber property for this sibling temporary file.
        if os.name == "nt":
            package.rename(output)
        else:
            os.link(package, output)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_subparsers(dest="operation", required=True)
    builder = operation.add_parser("export", help="Export selected published skills into a new ZIP")
    builder.add_argument(
        "--skill", required=True, action="append", help="Exact catalog skill ID. Repeat to select more."
    )
    builder.add_argument("--output", type=Path, required=True)
    verifier = operation.add_parser("verify", help="Verify the file inventory and digests of a skill ZIP")
    verifier.add_argument("package", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = export(ROOT, args.skill, args.output) if args.operation == "export" else verify(args.package)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as error:
        print(f"Package error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
