"""Run a verified Gitleaks binary against an exact local Git repository."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


class ScanError(ValueError):
    """A safely reportable history-scan setup failure."""


def digest(path: Path) -> str:
    """Hash the exact executable selected by the caller."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def scan_environment(git: Path, repository: Path) -> dict[str, str]:
    """Bind Git lookup and its process-scoped configuration to the request."""
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith(("GIT_", "GITLEAKS_"))}
    if sys.platform == "win32":
        system = env.get("SYSTEMROOT") or env.get("SystemRoot")
        if not system:
            raise ScanError("Windows system directory is unavailable")
        search_path = [str(git.parent), str(Path(system) / "System32"), system]
    else:
        search_path = [str(git.parent), os.defpath]
    env["PATH"] = os.pathsep.join(search_path)
    env.update(
        GIT_CONFIG_COUNT="2",
        GIT_CONFIG_KEY_0="safe.directory",
        GIT_CONFIG_VALUE_0=str(repository),
        GIT_CONFIG_KEY_1="core.longpaths",
        GIT_CONFIG_VALUE_1="true",
    )
    return env


def git_value(git: Path, repository: Path, env: dict[str, str], *args: str) -> str:
    """Read a local Git property and reject every diagnostic or failed command."""
    result = subprocess.run([str(git), "-C", str(repository), *args], env=env, capture_output=True, check=False)
    if result.returncode or result.stderr:
        raise ScanError("Git could not verify repository history")
    try:
        return result.stdout.decode("utf-8").strip()
    except UnicodeError as error:
        raise ScanError("Git returned invalid repository metadata") from error


def reject_ignore_file(root: Path) -> None:
    """Reject even a broken or untracked repository ignore file."""
    try:
        (root / ".gitleaksignore").lstat()
    except FileNotFoundError:
        return
    raise ScanError("Repository contains a Gitleaks ignore file")


def verify_repository(git: Path, repository: Path, env: dict[str, str]) -> tuple[bytes, str, str]:
    """Require the selected root, full history and a suppression-free configuration."""
    try:
        root = Path(git_value(git, repository, env, "rev-parse", "--show-toplevel")).resolve(strict=True)
        if root != repository or git_value(git, root, env, "rev-parse", "--is-shallow-repository") != "false":
            raise ScanError("Select the exact root of a non-shallow repository")
        head = git_value(git, root, env, "rev-parse", "--verify", "HEAD")
        refs = git_value(git, root, env, "for-each-ref", "--format=%(refname) %(objectname)")
        reject_ignore_file(root)
        config = root / ".gitleaks.toml"
        if config.is_symlink():
            raise ScanError("Gitleaks configuration must be a regular repository file")
        raw = config.read_bytes()
        settings = tomllib.loads(raw.decode("utf-8"))
        if settings != {"extend": {"useDefault": True}}:
            raise ScanError("Gitleaks configuration must enable all default rules without exclusions")
        return raw, head, refs
    except (OSError, ValueError) as error:
        if isinstance(error, ScanError):
            raise
        raise ScanError("Repository or scanner configuration could not be verified") from error


def run(gitleaks: Path, git: Path, repository: Path, expected_sha256: str) -> int:
    """Scan all refs and merge parents with redacted output and no inline exemptions."""
    executable = gitleaks.resolve(strict=True)
    git = git.resolve(strict=True)
    repository = repository.resolve(strict=True)
    expected_git_name = "git.exe" if sys.platform == "win32" else "git"
    if not executable.is_file() or not git.is_file() or git.name.lower() != expected_git_name:
        raise ScanError("Use explicit Gitleaks and Git executable paths")
    if digest(executable) != expected_sha256:
        raise ScanError("Gitleaks executable does not match the approved SHA-256")
    env = scan_environment(git, repository)
    config, head, refs = verify_repository(git, repository, env)
    git_hash = digest(git)
    with tempfile.TemporaryDirectory(prefix="gitleaks-history-") as directory:
        config_copy = Path(directory) / "config.toml"
        config_copy.write_bytes(config)
        command = [
            str(executable),
            "git",
            "--log-opts=--all HEAD --full-history --no-renames --no-ext-diff --no-textconv -m",
            "--config",
            str(config_copy),
            "--gitleaks-ignore-path",
            directory,
            "--ignore-gitleaks-allow",
            "--redact",
            "--verbose",
            "--no-banner",
            "--no-color",
            "--log-level",
            "warn",
            "--exit-code",
            "1",
            str(repository),
        ]
        result = subprocess.run(command, cwd=directory, env=env, check=False)
    if digest(executable) != expected_sha256 or digest(git) != git_hash:
        raise ScanError("A scanner executable changed during the scan")
    if verify_repository(git, repository, env) != (config, head, refs):
        raise ScanError("Repository history or configuration changed during the scan")
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    """Validate the worker arguments without printing sensitive input."""
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4:
        print("Invalid Gitleaks worker request", file=sys.stderr)
        return 2
    try:
        return run(Path(args[0]), Path(args[1]), Path(args[2]), args[3])
    except ScanError as error:
        print(str(error), file=sys.stderr)
        return 2
    except (OSError, subprocess.SubprocessError):
        print("Gitleaks history worker could not verify or complete the scan", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
