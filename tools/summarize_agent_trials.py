#!/usr/bin/env python3
"""Verify every planned matched attempt and publish descriptive coding-agent results."""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from _lib_b.io_utils import dumps_deterministic, read_json, write_json, write_text

STATUSES = {"task_passed", "task_failed", "harness_error", "invalid_scope", "timed_out"}
LIMITATIONS = [
    "One development task and three matched attempts per condition do not establish collection-wide effectiveness.",
    "Quality is checked externally; agent-written regression tests are not a coverage or mutation score.",
    "Token statistics are descriptive actual CLI usage, not priced cost, significance, or general efficiency claims.",
    "Input tokens include cached input; reasoning usage is retained separately, not added again to output tokens.",
    "Elapsed time is diagnostic only; unrelated host workloads were not controlled.",
    "Provider-resolved model snapshots are unavailable; the requested model is not a verified backend revision.",
    "This frozen block does not pool earlier exploratory probes or harness versions; their failures remain recorded separately.",
    "The grading process executes submitted Python on the host; it is not a hardened service for arbitrary untrusted submissions.",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evidence_path(directory: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("evidence names must be strings")
    name = PurePosixPath(relative)
    if name.is_absolute() or ".." in name.parts or "\\" in relative or ":" in relative or name.as_posix() != relative:
        raise ValueError("evidence names must be safe relative POSIX paths")
    path = directory / relative
    if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink():
        raise ValueError(f"external evidence: {relative}")
    return path


def evidence_bytes(directory: Path, relative: str) -> bytes:
    path = evidence_path(directory, relative)
    if path.is_file():
        return path.read_bytes()
    if path.exists():
        raise ValueError(f"evidence must be a file: {relative}")
    # The frozen runner recorded grader-created bytecode. Git rightly ignores
    # loose cache files; preserve their exact bytes in a nonexecuted transport.
    archive = directory / "bytecode-evidence.zip"
    if (
        "__pycache__" not in PurePosixPath(relative).parts
        or not relative.endswith(".pyc")
        or not archive.is_file()
        or archive.is_symlink()
    ):
        raise ValueError(f"missing evidence: {relative}")
    with zipfile.ZipFile(archive) as zipped:
        if sum(info.file_size for info in zipped.infolist()) > 16 * 1024 * 1024 or len(zipped.namelist()) != len(
            set(zipped.namelist())
        ):
            raise ValueError("bytecode evidence archive is oversized or ambiguous")
        try:
            return zipped.read(relative)
        except KeyError as exc:
            raise ValueError(f"missing bytecode evidence: {relative}") from exc


def package_bytecode(directory: Path, evidence: dict[str, str]) -> None:
    names = sorted(name for name in evidence if "__pycache__" in PurePosixPath(name).parts and name.endswith(".pyc"))
    if not names:
        return
    archive = directory / "bytecode-evidence.zip"
    if archive.exists():
        with zipfile.ZipFile(archive) as zipped:
            if zipped.namelist() != names or any(
                hashlib.sha256(zipped.read(name)).hexdigest() != evidence[name] for name in names
            ):
                raise ValueError("existing bytecode transport differs from the frozen evidence")
        return
    contents = {name: evidence_bytes(directory, name) for name in names}
    if any(hashlib.sha256(contents[name]).hexdigest() != evidence[name] for name in names):
        raise ValueError("cannot package changed bytecode evidence")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as zipped:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, contents[name])


def verify_result(directory: Path, protocol: dict[str, Any], protocol_hash: str, condition: str) -> dict[str, Any]:
    result = read_json(directory / "result.json")
    if not isinstance(result, dict):
        raise ValueError("trial result must be an object")
    expected = {
        "protocol_sha256": protocol_hash,
        "task_id": protocol["task"]["id"],
        "partition": protocol["task"]["partition"],
        "condition": condition,
        "model_requested": protocol["model"],
        "reasoning_effort_requested": protocol["reasoning_effort"],
    }
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError("attempt differs from its frozen protocol or assigned condition")
    if result.get("status") not in STATUSES:
        raise ValueError("unknown attempt outcome")
    evidence = result.get("evidence_sha256")
    if not isinstance(evidence, dict) or not {
        "launch.json",
        "transcript.jsonl",
        "prompt.txt",
        "stderr.txt",
        "patch.diff",
    }.issubset(evidence):
        raise ValueError("attempt evidence manifest is incomplete")
    for relative, digest in evidence.items():
        if hashlib.sha256(evidence_bytes(directory, relative)).hexdigest() != digest:
            raise ValueError(f"evidence hash changed: {relative}")
    launch = read_json(directory / "launch.json")
    if not isinstance(launch, dict) or launch.get("protocol_sha256") != protocol_hash:
        raise ValueError("launch used a different frozen protocol")
    grade = result.get("grader")
    if not isinstance(grade, dict):
        raise ValueError("external grader result is unavailable")
    checks = grade.get("checks", [])
    if not isinstance(checks, list) or any(
        not isinstance(check, dict) or type(check.get("passed")) is not bool for check in checks
    ):
        raise ValueError("external checks must contain explicit boolean outcomes")
    names = [check.get("case") for check in checks]
    if any(not isinstance(name, str) or not name for name in names) or len(names) != len(set(names)):
        raise ValueError("external checks must have unique nonempty case names")
    if checks and (
        grade.get("checks_total") != len(checks)
        or grade.get("checks_passed") != sum(check["passed"] for check in checks)
    ):
        raise ValueError("external check counts are inconsistent")
    if result["status"] == "task_passed" and (
        not checks
        or not all(check["passed"] for check in checks)
        or grade.get("status") != "task_passed"
        or result.get("process_exit_code") != 0
        or result.get("scope_violations") != []
        or result.get("evidence_collection_errors") != []
    ):
        raise ValueError("reported pass is contradicted by grading, execution, or collection evidence")
    usage = result.get("usage")
    if usage is not None:
        if not isinstance(usage, dict) or any(type(value) is not int or value < 0 for value in usage.values()):
            raise ValueError("usage must contain nonnegative integer counts; unavailable usage stays null")
        if (
            not {"input_tokens", "output_tokens"}.issubset(usage)
            or usage.get("cached_input_tokens", 0) > usage["input_tokens"]
        ):
            raise ValueError("usage token totals are incomplete or contradictory")
    return result


def summarize(protocol_path: Path, trials: Path, *, package_caches: bool = False) -> dict[str, Any]:
    protocol = read_json(protocol_path)
    protocol_hash = sha256(protocol_path)
    rows, planned_paths = [], set()
    repetitions = set()
    conditions = set(protocol["conditions"])
    for block in protocol["planned_order"]:
        repetition = block["repetition"]
        if (
            type(repetition) is not int
            or repetition < 1
            or repetition in repetitions
            or len(block["conditions"]) != len(conditions)
            or set(block["conditions"]) != conditions
        ):
            raise ValueError("every repetition must assign every condition exactly once")
        repetitions.add(repetition)
        for condition in block["conditions"]:
            if not condition.replace("-", "").replace("_", "").isalnum():
                raise ValueError("unsafe condition name")
            relative = f"repetition-{repetition}/{condition}"
            planned_paths.add(relative + "/result.json")
            directory = trials / relative
            if not (directory / "result.json").is_file():
                raise ValueError(f"planned attempt has not completed: {relative}")
            result = verify_result(directory, protocol, protocol_hash, condition)
            if package_caches:
                package_bytecode(directory, result["evidence_sha256"])
            rows.append(
                {
                    "repetition": repetition,
                    "condition": condition,
                    "status": result["status"],
                    "checks_passed": result["grader"].get("checks_passed"),
                    "checks_total": result["grader"].get("checks_total"),
                    "usage": result.get("usage"),
                    "elapsed_seconds_diagnostic_only": result.get("elapsed_seconds"),
                    "provider_model_snapshot": result.get("provider_model_snapshot"),
                    "result_path": relative + "/result.json",
                    "result_sha256": sha256(directory / "result.json"),
                    "bytecode_transport_sha256": sha256(directory / "bytecode-evidence.zip")
                    if (directory / "bytecode-evidence.zip").is_file()
                    else None,
                }
            )
    if not rows:
        raise ValueError("protocol contains no planned attempts")
    observed_paths = {path.relative_to(trials).as_posix() for path in trials.rglob("result.json")}
    if observed_paths != planned_paths:
        raise ValueError("trial directory includes unplanned results; refusing selective or duplicate accounting")
    summaries = {}
    for condition in sorted(conditions):
        matched = [row for row in rows if row["condition"] == condition]
        usage = [row["usage"] for row in matched if row["usage"] is not None]
        summaries[condition] = {
            "planned_attempts": len(matched),
            "status_counts": dict(sorted(Counter(row["status"] for row in matched).items())),
            "task_passes": sum(row["status"] == "task_passed" for row in matched),
            "usage_observed_attempts": len(usage),
            "usage_unavailable_attempts": len(matched) - len(usage),
            "token_statistics": {
                key: {
                    "sum": sum(record[key] for record in usage),
                    "median": statistics.median(record[key] for record in usage),
                    "min": min(record[key] for record in usage),
                    "max": max(record[key] for record in usage),
                }
                for key in ("input_tokens", "output_tokens")
            }
            if usage
            else None,
        }
    return {
        "report_version": 1,
        "protocol_sha256": protocol_hash,
        "task_id": protocol["task"]["id"],
        "partition": protocol["task"]["partition"],
        "model_requested": protocol["model"],
        "reasoning_effort_requested": protocol["reasoning_effort"],
        "task_count": 1,
        "planned_attempts": len(rows),
        "completed_attempts": len(rows),
        "conditions": summaries,
        "attempts": rows,
        "quality_superiority_established": False,
        "limitations": LIMITATIONS + protocol.get("limitations", []),
    }


def render(report: dict[str, Any]) -> str:
    lines = [
        "# Matched development trials",
        "",
        f"Task: `{report['task_id']}`. Requested model: `{report['model_requested']}` with `{report['reasoning_effort_requested']}` reasoning.",
        "",
        f"All {report['planned_attempts']} planned attempts are recorded. No quality superiority is established.",
        "",
        "| Condition | Task passes / planned | Observed usage | Input tokens, median [min–max] | Output tokens, median [min–max] |",
        "| --- | --- | --- | --- | --- |",
    ]
    for condition, values in report["conditions"].items():
        stats = values["token_statistics"]

        def token_range(key: str, stats: dict[str, Any] | None = stats) -> str:
            return (
                "unavailable"
                if stats is None
                else f"{stats[key]['median']:,} [{stats[key]['min']:,}–{stats[key]['max']:,}]"
            )

        lines.append(
            f"| {condition} | {values['task_passes']}/{values['planned_attempts']} | {values['usage_observed_attempts']}/{values['planned_attempts']} | {token_range('input_tokens')} | {token_range('output_tokens')} |"
        )
    lines += [
        "",
        "Input counts include cached input. Output counts are reported as returned by the CLI. These are descriptive tokens, not priced costs or statistically demonstrated efficiency gains.",
        "",
        "The conditions use a default agent, a pinned third-party Karpathy adaptation, and an experimental two-skill bundle. Earlier exploratory and harness-version failures are retained separately; see [experiment protocol](../../../docs/agent-trial-protocol.md).",
        "",
        "## Limits",
        "",
    ]
    lines += [f"- {limitation}" for limitation in report["limitations"]]
    return "\n".join(lines) + "\n"


def plots(report: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"svg.hashsalt": report["protocol_sha256"], "svg.fonttype": "none", "font.size": 10})
    conditions = sorted(report["conditions"])
    colors = ["#2563eb", "#059669", "#d97706"]
    figure, axis = plt.subplots(figsize=(7.6, 4.0), layout="constrained")
    values = [report["conditions"][condition] for condition in conditions]
    rates = [value["task_passes"] / value["planned_attempts"] for value in values]
    axis.bar(conditions, rates, color=colors[: len(conditions)])
    for index, value in enumerate(values):
        axis.text(index, rates[index] + 0.02, f"{value['task_passes']}/{value['planned_attempts']}", ha="center")
    axis.set(
        ylim=(0, 1.12),
        ylabel="Task pass fraction, all planned attempts",
        title="One development task; no demonstrated quality advantage",
    )
    figure.savefig(output / "quality.svg", metadata={"Date": None, "Creator": "summarize_agent_trials.py"})
    figure.savefig(output / "quality.png", dpi=150, metadata={"Software": "summarize_agent_trials.py"})
    plt.close(figure)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    for axis, key, title in zip(
        axes,
        ("input_tokens", "output_tokens"),
        ("Input tokens, including cached input", "Output tokens, as reported by CLI"),
        strict=True,
    ):
        for index, condition in enumerate(conditions):
            rows = [row for row in report["attempts"] if row["condition"] == condition and row["usage"] is not None]
            axis.scatter(
                [index + (i - (len(rows) - 1) / 2) * 0.1 for i in range(len(rows))],
                [row["usage"][key] for row in rows],
                color=colors[index % len(colors)],
                label=condition,
            )
        axis.set_xticks(range(len(conditions)), conditions)
        axis.set(ylabel="Tokens per attempt", title=title)
        axis.set_ylim(bottom=0)
    figure.suptitle("Every observed attempt; descriptive usage, no cost or significance claim")
    figure.savefig(output / "tokens.svg", metadata={"Date": None, "Creator": "summarize_agent_trials.py"})
    figure.savefig(output / "tokens.png", dpi=150, metadata={"Software": "summarize_agent_trials.py"})
    plt.close(figure)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--check", action="store_true", help="Reverify all attempts and compare existing JSON/Markdown without writing"
    )
    parser.add_argument(
        "--plots", action="store_true", help="Generate standalone SVG charts; requires the reports extra"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--package-bytecode",
        action="store_true",
        help="Preserve frozen cache-byte evidence in portable archives; never change result records",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check and (args.plots or args.package_bytecode):
            raise ValueError("--check does not write charts or bytecode transports")
        report = summarize(args.protocol, args.trials, package_caches=args.package_bytecode)
        if args.check:
            if (args.output_dir / "summary.json").read_text(encoding="utf-8") != dumps_deterministic(report) or (
                args.output_dir / "README.md"
            ).read_text(encoding="utf-8") != render(report):
                raise ValueError("published trial report differs from verified recorded attempts")
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            write_json(args.output_dir / "summary.json", report)
            write_text(args.output_dir / "README.md", render(report))
            if args.plots:
                plots(report, args.output_dir)
        print(
            json.dumps(
                {
                    "valid": True,
                    "completed_attempts": report["completed_attempts"],
                    "quality_superiority_established": False,
                }
            )
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
