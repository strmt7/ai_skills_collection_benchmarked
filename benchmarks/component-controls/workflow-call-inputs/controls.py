"""Exercise reusable and manual workflow input types with actionlint."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import re
import subprocess
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / "included/improved/skills/workflow-call-inputs/SKILL.md"
TEMPLATE = (
    ROOT
    / "included/skills/by-category/devops-cloud-operations/latest-release-devops/github-actions-generator"
    / "assets/templates/workflow/reusable_workflow.yml"
)
VERSION = "1.7.12"
ARCHIVES = {
    "Windows": ("windows_amd64.zip", "6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9"),
    "Linux": ("linux_amd64.tar.gz", "8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(directory: Path) -> Path:
    if platform.machine().lower() not in {"amd64", "x86_64"} or platform.system() not in ARCHIVES:
        raise ValueError("The pinned actionlint download supports Windows and Linux x86-64 only")
    suffix, expected = ARCHIVES[platform.system()]
    name = f"actionlint_{VERSION}_{suffix}"
    url = f"https://github.com/rhysd/actionlint/releases/download/v{VERSION}/{name}"
    request = urllib.request.Request(url, headers={"User-Agent": "workflow-call-inputs-component-controls/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        archive = response.read()
    if sha256(archive) != expected:
        raise ValueError("The downloaded actionlint archive differs from the pinned digest")
    executable_name = "actionlint.exe" if platform.system() == "Windows" else "actionlint"
    if suffix.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            executable = bundle.read(executable_name)
    else:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as bundle:
            member = bundle.extractfile(executable_name)
            if member is None:
                raise ValueError("The actionlint executable is missing from the archive")
            executable = member.read()
    path = directory / executable_name
    path.write_bytes(executable)
    path.chmod(0o755)
    return path


def run(actionlint: Path, directory: Path) -> dict[str, object]:
    version = subprocess.run([str(actionlint), "-version"], check=True, capture_output=True, text=True, timeout=30)
    if version.stdout.splitlines()[0] != VERSION:
        raise ValueError("Unexpected actionlint version")
    template = TEMPLATE.read_bytes().replace(b"\r\n", b"\n")
    if (
        sha256(template) != "b1182c8e00dff00587f462cdafb514c3fb45a7a4604090a8a93384c03777be1c"
        or b"type: [string/boolean/number/choice/environment]" not in template
    ):
        raise ValueError("The source template changed; review the baseline")
    skill = SKILL.read_text(encoding="utf-8")
    examples = re.findall(r"(?ms)^```yaml\n(.*?)^```\s*$", skill)
    if len(examples) != 1:
        raise ValueError("Expected one maintained YAML workflow example")
    cases = []
    for event in ("workflow_call", "workflow_dispatch"):
        for kind in ("boolean", "number", "string", "choice", "environment"):
            options = (
                "        options:\n          - example\n" if event == "workflow_dispatch" and kind == "choice" else ""
            )
            content = (
                f"name: Type control\non:\n  {event}:\n    inputs:\n      value:\n        type: {kind}\n{options}"
                "jobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n"
            )
            expected_diagnostic = (
                None if event == "workflow_dispatch" or kind in {"boolean", "number", "string"} else "invalid value"
            )
            cases.append((f"{event}-{kind}", content, expected_diagnostic))
    for kind, default, expected_diagnostic in (
        ("boolean", "false", None),
        ("boolean", "maybe", "default value must be true or false"),
        ("number", "2", None),
        ("number", "abc", "cannot be parsed as a float"),
        ("string", "abc", None),
    ):
        content = (
            f"name: Default control\non:\n  workflow_call:\n    inputs:\n      value:\n        type: {kind}\n"
            f"        default: {default}\njobs:\n  check:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo ok\n"
        )
        cases.append((f"workflow_call-{kind}-default-{default}", content, expected_diagnostic))
    cases.append(("maintained-example", examples[0], None))
    outcomes = []
    for name, content, expected_diagnostic in cases:
        path = directory / f"{name}.yml"
        path.write_text(content, encoding="utf-8", newline="\n")
        proc = subprocess.run(
            [str(actionlint), "-no-color", str(path)], capture_output=True, text=True, timeout=30, check=False
        )
        if (proc.returncode == 0) != (expected_diagnostic is None):
            raise ValueError(f"{name}: unexpected actionlint result {proc.returncode}: {proc.stdout} {proc.stderr}")
        if expected_diagnostic is not None and (
            expected_diagnostic not in proc.stdout or "workflow_call" not in proc.stdout
        ):
            raise ValueError(f"{name}: expected the workflow_call input diagnostic")
        outcomes.append(
            {
                "case": name,
                "input_sha256": sha256(content.encode()),
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }
        )
    return {
        "actionlint_version": VERSION,
        "actionlint_executable_sha256": sha256(actionlint.read_bytes()),
        "platform": platform.system(),
        "template_sha256": sha256(template),
        "skill_sha256": sha256(SKILL.read_bytes()),
        "cases": outcomes,
        "scope": "Static input-type component controls; no hosted workflow execution or agent trial.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    binaries = parser.add_mutually_exclusive_group(required=True)
    binaries.add_argument("--actionlint", type=Path, help="Path to actionlint 1.7.12")
    binaries.add_argument(
        "--download", action="store_true", help="Download the digest-pinned official binary to a temp dir"
    )
    parser.add_argument("--output", type=Path, help="Write results to this path instead of stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="workflow-call-inputs-") as temporary:
        directory = Path(temporary)
        actionlint = download(directory) if args.download else args.actionlint.resolve()
        result = run(actionlint, directory)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
