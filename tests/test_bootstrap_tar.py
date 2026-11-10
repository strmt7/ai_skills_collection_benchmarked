"""Exercise the actual managed archive reader in the admitted PowerShell runtime."""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = r"""$ErrorActionPreference='Stop'
. (Join-Path $args[0] 'toolchains/bootstrap/ArchiveLayers.ps1')
function Native-Path([string]$Path) { return $Path }
function Assert-OrdinaryPath([string]$Path) {
    $cursor=$Path
    while ($cursor) {
        if ((Test-Path -LiteralPath $cursor) -and ((Get-Item -LiteralPath $cursor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Test fixture contains a reparse point' }
        $cursor=[IO.Path]::GetDirectoryName($cursor)
    }
}
function Get-Digest([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$pin=Get-Content -LiteralPath $args[2] -Raw | ConvertFrom-Json
Expand-PinnedTar $args[1] $args[3] $pin
"""


@pytest.fixture
def archive_reader(tmp_path: Path):
    diagnostics = os.environ.get("AI_SKILLS_BOOTSTRAP_DIAGNOSTICS")
    if sys.platform != "win32" or not diagnostics:
        pytest.skip("Run through ./dev.ps1 python on Windows to test the admitted native archive reader")
    engine = json.loads((Path(diagnostics) / "source.json").read_bytes())["bootstrap_engine"]
    executable = Path(engine["path"])
    assert hashlib.sha256(executable.read_bytes()).hexdigest() == engine["sha256"]
    driver = tmp_path / "reader.ps1"
    driver.write_text(DRIVER, encoding="utf-8")

    def invoke(members: list[tuple[str, bytes, bytes]], expected: dict[str, bytes]):
        archive = tmp_path / "fixture.tar.gz"
        with tarfile.open(archive, "w:gz") as stream:
            for name, content, kind in members:
                member = tarfile.TarInfo(name)
                member.type = kind
                if kind == tarfile.SYMTYPE:
                    member.linkname = "outside"
                member.size = len(content) if kind == tarfile.REGTYPE else 0
                stream.addfile(member, io.BytesIO(content))
        pin = tmp_path / "pin.json"
        pin.write_text(
            json.dumps(
                {
                    "files": {
                        name: {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                        for name, data in expected.items()
                    }
                }
            ),
            encoding="utf-8",
        )
        output = tmp_path / "payload"
        output.mkdir()
        process = subprocess.run(
            [
                str(executable),
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(driver),
                str(ROOT),
                str(archive),
                str(pin),
                str(output),
            ],
            capture_output=True,
            timeout=30,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return process, output

    return invoke


def test_managed_tar_extracts_complete_nested_and_empty_files(archive_reader):
    expected = {"package/bin/tool.exe": b"owned fixture", "package/empty": b""}
    members = [
        ("package/", b"", tarfile.DIRTYPE),
        *[(name, value, tarfile.REGTYPE) for name, value in expected.items()],
    ]
    process, output = archive_reader(members, expected)
    assert process.returncode == 0, process.stderr.decode(errors="replace")
    assert {
        path.relative_to(output).as_posix(): path.read_bytes() for path in output.rglob("*") if path.is_file()
    } == expected


@pytest.mark.parametrize(
    ("members", "expected", "message"),
    [
        ([("../escape", b"x", tarfile.REGTYPE)], {"package/file": b"x"}, "noncanonical"),
        ([("package/file", b"x", tarfile.SYMTYPE)], {"package/file": b"x"}, "unsupported type"),
        ([("package/file", b"x", tarfile.REGTYPE)] * 2, {"package/file": b"x"}, "duplicate"),
        ([("package/extra", b"x", tarfile.REGTYPE)], {"package/file": b"x"}, "undeclared member"),
        ([], {"package/file": b"x"}, "missing declared"),
        ([("package/file", b"y", tarfile.REGTYPE)], {"package/file": b"x"}, "integrity differs"),
        ([("package/file", b"xx", tarfile.REGTYPE)], {"package/file": b"x"}, "size differs"),
        ([("undeclared/", b"", tarfile.DIRTYPE)], {"package/file": b"x"}, "undeclared directory"),
    ],
)
def test_managed_tar_rejects_invalid_payload(archive_reader, members, expected, message):
    process, output = archive_reader(members, expected)
    assert process.returncode != 0
    assert message in (process.stdout + process.stderr).decode(errors="replace")
    assert not (output.parent / "escape").exists()
