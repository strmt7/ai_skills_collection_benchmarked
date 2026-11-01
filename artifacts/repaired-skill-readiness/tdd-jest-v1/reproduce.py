from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

EXPECTED_SKILL = "63249998befbdbbf2f7d2f089c9cd7a9912f26ddc8fdf04ab1248c82614b43ac"
EXPECTED_COMMIT = "846ffb75da9a5f4e677d927af1ad4a1951652267"
EXPECTED_JEST = "30.5.2"
SOURCE_JS = "function classify(value) {\n  if (value > 0) return 'positive';\n  return 'nonpositive';\n}\nmodule.exports = classify;\n"
TEST_JS = "const classify = require('./src');\ntest('positive', () => expect(classify(1)).toBe('positive'));\n"
FULL_TEST_JS = TEST_JS + "test('nonpositive', () => expect(classify(0)).toBe('nonpositive'));\n"


def run(
    skill: Path, overlay: Path, jest: Path, logs: Path | None, expected_sha: str, source_commit: str, node_command: str
) -> dict[str, Any]:
    data = skill.read_bytes().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha:
        raise ValueError("skill does not match the pinned source")
    configs = []
    for block in re.findall(r"```json\s*\n(.*?)\n```", data.decode("utf-8"), re.S):
        try:
            config = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(config, dict) and isinstance(config.get("jest"), dict) and "coverageThresholds" in config["jest"]:
            configs.append(config)
    if len(configs) != 1:
        raise ValueError("expected one source threshold example")
    node = shutil.which(node_command)
    if node is None:
        raise ValueError("Node is required")
    jest = jest.resolve(strict=True)
    version = subprocess.run(
        [node, str(jest), "--version"], capture_output=True, text=True, encoding="utf-8", check=True, timeout=30
    ).stdout.strip()
    if version != EXPECTED_JEST:
        raise ValueError(f"expected Jest {EXPECTED_JEST}; found {version}")
    node_version = subprocess.run(
        [node, "--version"], capture_output=True, text=True, encoding="utf-8", check=True, timeout=30
    ).stdout.strip()
    lock = jest.parents[3] / "package-lock.json"
    if not lock.is_file():
        raise ValueError("the isolated Jest installation must retain its package-lock.json")
    lock_hash = hashlib.sha256(lock.read_bytes()).hexdigest()
    corrected = copy.deepcopy(configs[0])
    settings = corrected["jest"]
    settings["coverageThreshold"] = settings.pop("coverageThresholds")
    overlay_data = overlay.read_bytes().replace(b"\r\n", b"\n")
    overlay_blocks = re.findall(r"```json\s*\n(.*?)\n```", overlay_data.decode("utf-8"), re.S)
    if len(overlay_blocks) != 1:
        raise ValueError("expected one overlay JSON example")
    overlay_config = json.loads(overlay_blocks[0])
    if overlay_config != corrected:
        raise ValueError("overlay example differs from the source with the option name corrected")
    variants = {
        "source_low": (configs[0], TEST_JS),
        "overlay_low": (overlay_config, TEST_JS),
        "overlay_full": (overlay_config, FULL_TEST_JS),
    }
    results = {}
    if logs is not None:
        logs.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for name, (configuration, test_source) in variants.items():
            project = root / name
            project.mkdir()
            (project / "src.js").write_text(SOURCE_JS, encoding="utf-8", newline="\n")
            (project / "src.test.js").write_text(test_source, encoding="utf-8", newline="\n")
            package = {"name": "jest-threshold-control", "version": "1.0.0", "private": True, **configuration}
            (project / "package.json").write_text(json.dumps(package) + "\n", encoding="utf-8", newline="\n")
            args = [
                node,
                str(jest),
                "--config",
                str(project / "package.json"),
                "--runInBand",
                "--coverage",
                "--collectCoverageFrom=src.js",
                "--coverageReporters=json-summary",
                "--json",
                f"--outputFile={project / 'results.json'}",
            ]
            proc = subprocess.run(args, cwd=project, capture_output=True, timeout=60, check=False)
            if logs is not None:
                (logs / f"{name}.stdout").write_bytes(proc.stdout)
                (logs / f"{name}.stderr").write_bytes(proc.stderr)
                shutil.copyfile(project / "results.json", logs / f"{name}.results.json")
                shutil.copyfile(project / "coverage/coverage-summary.json", logs / f"{name}.coverage.json")
            stderr = proc.stderr.decode("utf-8", errors="replace")
            test_result = json.loads((project / "results.json").read_text(encoding="utf-8"))
            coverage = json.loads((project / "coverage/coverage-summary.json").read_text(encoding="utf-8"))["total"]
            results[name] = {
                "exit_code": proc.returncode,
                "passed_tests": test_result["numPassedTests"],
                "failed_tests": test_result["numFailedTests"],
                "unknown_plural_warning": 'Unknown option "coverageThresholds"' in stderr,
                "threshold_failure": 'does not meet "global" threshold' in stderr,
                "coverage_percent": {k: coverage[k]["pct"] for k in ("statements", "branches", "functions", "lines")},
            }
    return {
        "artifact_kind": "independent_runtime_readiness_component",
        "source_skill_sha256": digest,
        "source_commit": source_commit,
        "overlay_skill_sha256": hashlib.sha256(overlay_data).hexdigest(),
        "jest_version": version,
        "node_version": node_version,
        "npm_lock_sha256": lock_hash,
        "results": results,
        "agent_efficacy_scored": False,
        "limitations": [
            "Synthetic test project; no agent evaluation.",
            "Corrected configuration changes only the option name.",
            "The full npm dependency lock and native logs are retained outside the repository.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--expected-sha", default=EXPECTED_SKILL)
    parser.add_argument("--source-commit", default=EXPECTED_COMMIT)
    parser.add_argument("--jest", type=Path, required=True)
    parser.add_argument("--node", default="node", help="Node executable or explicit path")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--logs", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if not re.fullmatch(r"[0-9a-f]{64}", args.expected_sha) or not re.fullmatch(
            r"[0-9a-f]{40}", args.source_commit
        ):
            raise ValueError("expected-sha and source-commit must be lowercase hexadecimal hashes")
        result = (
            json.dumps(
                run(args.skill, args.overlay, args.jest, args.logs, args.expected_sha, args.source_commit, args.node),
                indent=2,
            )
            + "\n"
        )
        if args.check:
            if args.output.read_text(encoding="utf-8") != result:
                raise ValueError("recorded control differs from this execution")
        else:
            args.output.write_text(result, encoding="utf-8", newline="\n")
        print(result)
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
