"""Run source-bound Java Event Hubs batch controls without connecting to Azure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXAMPLE = ROOT / (
    "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/"
    "azure-eventhub-java-batching/examples"
)
FILES = (
    "pom.xml",
    "dependency-tree.json",
    "src/main/java/example/EventBatchSender.java",
    "src/test/java/com/azure/messaging/eventhubs/EventBatchSenderTest.java",
)
CASES = {
    "emptyInputDoesNotCreateOrSendBatch",
    "singleEventIsSentOnce",
    "batchCreationFailurePropagatesBeforeSending",
    "rolloverPreservesEveryEventInOrder",
    "oversizedFirstEventIsReportedWithoutSendingEmptyBatch",
    "oversizedLaterEventIsReportedAfterPriorBatchIsSent",
    "sdkOversizeExceptionIsNotSilencedOrSent",
    "originalRetryPatternOmitsRejectedEvent",
    "sendFailureStopsProcessingAndPropagates",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(maven: Path, java_home: Path, pwsh: Path, output: Path, java_major: int) -> dict[str, Any]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    java = java_home / "bin" / ("java.exe" if os.name == "nt" else "java")
    if not java.is_file():
        raise ValueError("The supplied Java home does not contain the Java executable")
    with tempfile.TemporaryDirectory(prefix="eventhub-java-") as temporary:
        workspace = Path(temporary)
        project = workspace / "project"
        for name in FILES:
            target = project / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(EXAMPLE / name, target)
        script = workspace / "invoke-maven.ps1"
        script.write_text(
            "param([string]$Maven, [string]$Project, [string]$Repository, [string]$Mode, [string]$Tree)\n"
            '$ErrorActionPreference = "Stop"\n'
            'if ($Mode -eq "version") { & $Maven -v; exit $LASTEXITCODE }\n'
            '$argsList = @("-B", "-f", $Project, "-Dmaven.repo.local=$Repository")\n'
            'if ($Mode -eq "tree") {\n'
            '  $argsList += @("org.apache.maven.plugins:maven-dependency-plugin:3.11.0:tree", '
            '"-DoutputType=json", "-DoutputFile=$Tree")\n'
            '} else { $argsList += "test" }\n'
            "& $Maven @argsList\nexit $LASTEXITCODE\n",
            encoding="utf-8",
            newline="\n",
        )
        env = dict(os.environ)
        for name in ("MAVEN_OPTS", "MAVEN_ARGS", "JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS"):
            env.pop(name, None)
        env.update(JAVA_HOME=str(java_home), MAVEN_USER_HOME=str(workspace / "maven-home"), MAVEN_SKIP_RC="1")
        java_result = subprocess.run([str(java), "--version"], cwd=project, env=env, capture_output=True, timeout=30)
        java_version = java_result.stdout.decode("utf-8").splitlines()[0] if java_result.stdout else ""
        if java_result.returncode or not re.match(rf"^(?:openjdk|java) {java_major}(?:[.\s+]|$)", java_version):
            raise ValueError(f"Expected Java {java_major}; inspect the supplied Java home")

        def invoke(mode: str) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run(
                [
                    str(pwsh),
                    "-NoLogo",
                    "-NoProfile",
                    "-NonInteractive",
                    "-File",
                    str(script),
                    "-Maven",
                    str(maven),
                    "-Project",
                    str(project / "pom.xml"),
                    "-Repository",
                    str(workspace / "maven-repository"),
                    "-Mode",
                    mode,
                    "-Tree",
                    str(workspace / "actual-tree.json"),
                ],
                cwd=project,
                env=env,
                capture_output=True,
                timeout=600,
            )

        version_result = invoke("version")
        version_lines = version_result.stdout.decode("utf-8", errors="replace").splitlines()
        maven_version = version_lines[0] if version_lines else ""
        if version_result.returncode or not maven_version.startswith("Apache Maven 3.10.0 "):
            raise ValueError("Expected Apache Maven 3.10.0")
        streams = {}
        for mode in ("test", "tree"):
            result = invoke(mode)
            for name in ("stdout", "stderr"):
                path = output / f"{mode}.{name}"
                path.write_bytes(getattr(result, name))
                streams[f"{mode}_{name}_sha256"] = sha(path)
            if result.returncode:
                raise ValueError(f"Maven {mode} failed; inspect retained streams")
        tree = json.loads((workspace / "actual-tree.json").read_text(encoding="utf-8"))
        expected_tree = json.loads((project / "dependency-tree.json").read_text(encoding="utf-8"))
        if tree != expected_tree:
            (output / "actual-tree.json").write_text(json.dumps(tree, indent=2) + "\n", encoding="utf-8")
            raise ValueError("Resolved dependency graph differs from the recorded snapshot")
        report_xml = project / "target/surefire-reports/TEST-com.azure.messaging.eventhubs.EventBatchSenderTest.xml"
        suite = ET.parse(report_xml).getroot()
        cases = suite.findall("testcase")
        names = {case.attrib["name"] for case in cases}
        if (
            names != CASES
            or len(cases) != len(CASES)
            or suite.attrib["tests"] != str(len(CASES))
            or any(suite.attrib[key] != "0" for key in ("failures", "errors", "skipped"))
        ):
            raise ValueError("Expected batch controls did not all pass")
        report = {
            "schema_version": 1,
            "platform": platform.system(),
            "java_version": java_version,
            "maven_version": maven_version,
            "test_cases": sorted(names),
            "dependency_tree_matched": True,
            "file_sha256": {name: sha(project / name) for name in FILES},
            **streams,
            "azure_service_called": False,
            "agent_performance_tested": False,
        }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maven", type=Path, required=True)
    parser.add_argument("--java-home", type=Path, required=True)
    parser.add_argument("--pwsh", type=Path, required=True)
    parser.add_argument("--java-major", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if any(not path.is_absolute() or not path.is_file() for path in (args.maven, args.pwsh)):
        raise ValueError("--maven and --pwsh must be absolute paths to existing executables")
    if not args.java_home.is_absolute() or not args.java_home.is_dir():
        raise ValueError("--java-home must be an absolute path to an existing directory")
    result = run(args.maven.resolve(), args.java_home.resolve(), args.pwsh.resolve(), args.output, args.java_major)
    print(json.dumps({"ok": True, "tests": len(result["test_cases"]), "azure_service_called": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
