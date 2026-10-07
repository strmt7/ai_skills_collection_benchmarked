#!/usr/bin/env python3
"""Run immutable native source fixtures inside the existing bounded backend."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

TOOLS = Path("/opt/LLVM-23.1.3-Linux-X64/bin")
FIXTURES = Path("/opt/llvm-controls")


def invoke(command, directory, **environment):
    result = subprocess.run(
        [str(x) for x in command],
        cwd=directory,
        env={
            **os.environ,
            "LLVM_PROFILE_FILE": str(directory / "unused-%p.profraw"),
            "ASAN_OPTIONS": "detect_leaks=0",
            **environment,
        },
        capture_output=True,
        timeout=10,
        check=False,
    )
    return {
        "command": [str(x) for x in command],
        "returncode": result.returncode,
        "stdout": result.stdout.decode("utf-8", errors="replace"),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }


def run(request):
    checks = []
    observations = {}
    with tempfile.TemporaryDirectory(prefix="llvm-controls-") as temporary:
        directory = Path(temporary)
        versions = {
            name: invoke([TOOLS / name, "--version"], directory) for name in ["clang++", "llvm-cov", "llvm-profdata"]
        }
        observations["versions"] = versions
        if all(x["returncode"] == 0 and "23.1.3" in x["stdout"] for x in versions.values()):
            checks.append("matching_stable_compiler_and_profile_tools")
        seed = directory / "division-zero"
        seed.write_bytes(bytes(8))
        for name in ["division-O0", "division-O2", "division-checked"]:
            observations[name] = invoke([FIXTURES / name, "-rss_limit_mb=256", "-timeout=2", seed], directory)
        if (
            observations["division-O0"]["returncode"] != 0
            and "UndefinedBehaviorSanitizer: FPE" in observations["division-O0"]["stderr"]
        ):
            checks.append("original_division_zero_crashes_without_optimization")
        if observations["division-O2"]["returncode"] == 0:
            checks.append("original_unused_division_eliminated_at_O2")
        if (
            observations["division-checked"]["returncode"] != 0
            and "division by zero" in observations["division-checked"]["stderr"]
        ):
            checks.append("defined_byte_decode_and_consumed_result_detect_zero_with_ubsan")
        valid = directory / "division-valid"
        valid.write_bytes(bytes([8, 0, 0, 0, 2, 0, 0, 0]))
        observations["valid_division"] = invoke(
            [FIXTURES / "division-checked", "-rss_limit_mb=256", "-timeout=2", valid], directory
        )
        if observations["valid_division"]["returncode"] == 0:
            checks.append("same_checked_target_accepts_valid_denominator")
        replay = FIXTURES / "replay-O3"
        unreadable = directory / "unreadable-corpus"
        unreadable.mkdir()
        (unreadable / "denied").write_bytes(b"A")
        (unreadable / "denied").chmod(0)
        observations["unreadable_replay"] = invoke([replay, unreadable], directory)
        (unreadable / "denied").chmod(0o600)
        result = observations["unreadable_replay"]
        if (
            result["returncode"] == 0
            and "Failed to open file" in result["stdout"]
            and "target-size=" not in result["stdout"]
        ):
            checks.append("original_replay_reports_success_for_unreadable_input")
        long_path = directory
        for _ in range(4):
            long_path = long_path / ("d" * 230)
            long_path.mkdir()
        (long_path / ("f" * 230)).write_bytes(b"A")
        observations["truncated_path_replay"] = invoke([replay, long_path], directory)
        result = observations["truncated_path_replay"]
        if (
            result["returncode"] == 0
            and "Failed to open file" in result["stdout"]
            and "target-size=" not in result["stdout"]
        ):
            checks.append("original_replay_truncates_valid_long_path_and_still_succeeds")
        empty = directory / "empty-corpus"
        empty.mkdir()
        (empty / "empty").write_bytes(b"")
        observations["empty_replay"] = invoke([replay, empty], directory)
        if (
            observations["empty_replay"]["returncode"] == 0
            and "target-size=0" in observations["empty_replay"]["stdout"]
        ):
            checks.append("glibc_empty_input_replay_works_here_not_portability_proof")
        bounded = FIXTURES / "replay-bounded"
        good = directory / "bounded-valid"
        good.write_bytes(b"A")
        denied = unreadable / "denied"
        denied.chmod(0)
        exact = directory / "bounded-exact-limit"
        exact.write_bytes(b"A" * (1024 * 1024))
        oversized = directory / "bounded-over-limit"
        oversized.write_bytes(b"A" * (1024 * 1024 + 1))
        link = directory / "bounded-symlink"
        link.symlink_to(good)
        cases = [
            ("valid", good, 1),
            ("empty", empty / "empty", 0),
            ("long_path", long_path / ("f" * 230), 1),
            ("exact_limit", exact, 1024 * 1024),
            ("unreadable", denied, None),
            ("oversized", oversized, None),
            ("missing", directory / "does-not-exist", None),
            ("symlink", link, None),
            ("directory", unreadable, None),
        ]
        for name, path, size in cases:
            result = invoke([bounded, path], directory)
            observations[f"bounded_{name}"] = result
            if size is None:
                if result["returncode"] == 2 and "target-size=" not in result["stdout"]:
                    checks.append(f"bounded_driver_rejects_{name}_before_target")
            elif (
                result["returncode"] == 0
                and f"target-size={size}\n" in result["stdout"]
                and f"replayed-bytes={size} callback=0\n" in result["stdout"]
            ):
                checks.append(f"bounded_driver_replays_{name}_completely")
        denied.chmod(0o600)
        profiles = []
        for label in ["A", "B"]:
            corpus = directory / f"corpus-{label}"
            corpus.mkdir()
            (corpus / "seed").write_bytes(label.encode("ascii"))
            raw, indexed = directory / f"{label}.profraw", directory / f"{label}.profdata"
            executed = invoke([replay, corpus], directory, LLVM_PROFILE_FILE=str(raw))
            merged = invoke([TOOLS / "llvm-profdata", "merge", "-sparse", raw, "-o", indexed], directory)
            exported = invoke(
                [TOOLS / "llvm-cov", "export", replay, f"-instr-profile={indexed}", "-format=text"], directory
            )
            if executed["returncode"] or merged["returncode"] or exported["returncode"]:
                raise ValueError("native coverage collection failed")
            profiles.append(indexed)
            observations[f"coverage-{label}"] = {
                "execute": executed,
                "merge": merged,
                "export": exported,
                "parsed": json.loads(exported["stdout"]),
            }
        if all(observations[f"coverage-{x}"]["parsed"]["type"] == "llvm.coverage.json.export" for x in ["A", "B"]):
            checks.append("O3_source_based_profiles_export_parseable_json")
        lcov = invoke(
            [TOOLS / "llvm-cov", "export", replay, f"-instr-profile={profiles[0]}", "-format=lcov"], directory
        )
        observations["lcov"] = lcov
        try:
            json.loads(lcov["stdout"])
        except json.JSONDecodeError:
            if lcov["returncode"] == 0 and "SF:" in lcov["stdout"]:
                checks.append("lcov_export_is_not_json")
        duplicated = invoke(
            [TOOLS / "llvm-cov", "export", replay, f"-instr-profile={profiles[1]}", f"-instr-profile={profiles[0]}"],
            directory,
        )
        observations["duplicate_profiles"] = duplicated
        if duplicated["returncode"] != 0 or json.loads(duplicated["stdout"]) == observations["coverage-A"]["parsed"]:
            checks.append("repeating_profile_argument_does_not_create_differential_coverage")
        combined = directory / "combined.profdata"
        observations["merge_both"] = invoke(
            [TOOLS / "llvm-profdata", "merge", "-sparse", *profiles, "-o", combined], directory
        )
        exported = invoke([TOOLS / "llvm-cov", "export", replay, f"-instr-profile={combined}"], directory)
        observations["combined_export"] = exported
        parsed = json.loads(exported["stdout"])

        def target(export):
            return next(f for f in export["data"][0]["files"] if f["filename"].endswith("/target.cc"))

        separate = [
            target(observations[f"coverage-{x}"]["parsed"])["summary"]["regions"]["covered"] for x in ["A", "B"]
        ]
        together = target(parsed)["summary"]["regions"]["covered"]
        if observations["merge_both"]["returncode"] == 0 and exported["returncode"] == 0 and together > max(separate):
            checks.append("matching_profile_merge_preserves_both_distinct_target_paths")
        observations["region_counts"] = {
            "separate": separate,
            "combined": together,
            "total": target(parsed)["summary"]["regions"]["count"],
        }
        build_receipt = json.loads((FIXTURES / "build-receipt.json").read_text())
    return {
        "checks": checks,
        "observations": observations,
        "build_receipt": build_receipt,
        "uid": os.getuid(),
        "agent_processes": 0,
        "temporary_directory_removed": not directory.exists(),
        "leak_detection_disabled": True,
        "runtime_compilation": False,
    }
