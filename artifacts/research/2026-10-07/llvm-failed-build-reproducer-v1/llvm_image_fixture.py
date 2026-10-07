#!/usr/bin/env python3
"""Build fixed source-contract fixtures inside a trusted offline LLVM image."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

from compression import zstd

TOP = "LLVM-23.1.3-Linux-X64"
BINARIES = {"clang-23", "clang", "clang++", "llvm-cov", "llvm-profdata", "llvm-symbolizer", "ld.lld", "lld"}
ROOT = Path("/opt/llvm-controls")
CLANG = f"/opt/{TOP}/bin/clang++"


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    selected = []
    total = 0
    with (
        zstd.ZstdFile("/tmp/llvm.tar.zst", options={zstd.DecompressionParameter.window_log_max: 31}) as stream,
        tarfile.open(fileobj=stream, mode="r|") as archive,
    ):
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or path.parts[0] != TOP:
                raise ValueError("noncontained release entry")
            parts = path.parts[1:]
            keep = (
                len(parts) == 2
                and parts[0] == "bin"
                and parts[1] in BINARIES
                or parts[:2] == ("lib", "clang")
                or len(parts) == 2
                and parts[0] == "lib"
                and parts[1].startswith("libclang-cpp.so")
            )
            if not keep:
                continue
            total += member.size
            if total > 1024**3 or not (member.isfile() or member.isdir() or member.issym()):
                raise ValueError("unexpected release member type or selected size")
            archive.extract(member, "/opt", filter="data")
            target = Path("/opt") / path
            selected.append(
                {
                    "path": path.as_posix(),
                    "bytes": member.size,
                    "link": member.linkname,
                    "sha256": digest(target) if member.isfile() else None,
                }
            )
    ROOT.mkdir()
    libfuzzer = Path("/tmp/libfuzzer.md").read_text()
    coverage = Path("/tmp/coverage.md").read_text()
    division = re.search(
        r"```c\+\+\n(#include <stdint.h>\n#include <stddef.h>\n\ndouble divide.*?)\n```", libfuzzer, re.S
    )
    replay = re.search(r"```cpp\n(// execute-rt\.cc.*?)\n```", coverage, re.S)
    if division is None or replay is None:
        raise ValueError("original fixture block missing")
    (ROOT / "original_division.cc").write_text(division[1] + "\n")
    (ROOT / "original_replay.cc").write_text(replay[1] + "\n")
    (ROOT / "target.cc").write_text(
        "#include <stdint.h>\n#include <stddef.h>\n#include <stdio.h>\n"
        'extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {\n'
        '  printf("target-size=%zu\\n", size);\n'
        "  if (!size) return 0;\n"
        '  if (data[0] == 65) puts("branch-A");\n'
        '  else if (data[0] == 66) puts("branch-B");\n'
        '  else puts("branch-other");\n'
        "  return 0;\n}\n"
    )
    (ROOT / "safe_division.cc").write_text(
        "#include <stdint.h>\n#include <stddef.h>\n"
        "static uint32_t little_endian(const uint8_t *p) {\n"
        "  return uint32_t(p[0]) | (uint32_t(p[1]) << 8) | (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);\n}\n"
        'extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {\n'
        "  if (size != 8) return 0;\n"
        "  volatile uint32_t result = little_endian(data) / little_endian(data + 4);\n"
        "  (void) result;\n  return 0;\n}\n"
    )
    commands = [
        [CLANG, "-O0", "-fsanitize=fuzzer", "original_division.cc", "-o", "division-O0"],
        [CLANG, "-O2", "-fsanitize=fuzzer", "original_division.cc", "-o", "division-O2"],
        [
            CLANG,
            "-O2",
            "-g",
            "-fsanitize=fuzzer,address,undefined",
            "-fno-sanitize-recover=all",
            "safe_division.cc",
            "-o",
            "division-checked",
        ],
        [
            CLANG,
            "-O3",
            "-fprofile-instr-generate",
            "-fcoverage-mapping",
            "original_replay.cc",
            "target.cc",
            "-o",
            "replay-O3",
        ],
    ]
    builds = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=120, check=False)
        builds.append(
            {
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout.decode(),
                "stderr": result.stderr.decode(),
            }
        )
        if result.returncode:
            print(json.dumps(builds, indent=2))
            raise ValueError("fixed native fixture compilation failed")
    receipt = {
        "selected_release_members": selected,
        "selected_bytes": total,
        "builds": builds,
        "source_sha256": {p.name: digest(p) for p in ROOT.glob("*.cc")},
        "binaries_sha256": {p.name: digest(p) for p in ROOT.iterdir() if p.is_file() and p.suffix != ".cc"},
    }
    (ROOT / "build-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
