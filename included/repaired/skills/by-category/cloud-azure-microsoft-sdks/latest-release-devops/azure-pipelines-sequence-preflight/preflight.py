"""Check literal Azure Pipelines sequence-entry shapes without claiming schema validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

STEP_TYPES = frozenset(
    {
        "task",
        "script",
        "powershell",
        "pwsh",
        "bash",
        "checkout",
        "download",
        "downloadBuild",
        "getPackage",
        "publish",
        "template",
        "reviewApp",
    }
)


def _expression(value: str) -> bool:
    return value.lstrip().startswith("${{")


class ShapeScan:
    """Inspect only statically visible stage, job and step sequence entries."""

    def __init__(self) -> None:
        self.issues: list[dict[str, Any]] = []
        self.deferred: list[dict[str, Any]] = []
        self.sequences_checked = 0
        self.entries_checked = 0

    def note(self, target: list[dict[str, Any]], node: Node, path: str, message: str) -> None:
        target.append(
            {"path": path, "line": node.start_mark.line + 1, "column": node.start_mark.column + 1, "message": message}
        )

    def fields(self, node: MappingNode, path: str) -> dict[str, Node]:
        result: dict[str, Node] = {}
        for key, value in node.value:
            if not isinstance(key, ScalarNode):
                self.note(self.deferred, key, path, "A complex mapping key requires Azure validation")
            elif _expression(key.value):
                self.note(self.deferred, key, path, "A template expression requires Azure expansion")
            elif key.value in result:
                self.note(self.deferred, key, path, "A duplicate mapping key requires Azure validation")
            else:
                result[key.value] = value
        return result

    def sequence(self, node: Node, kind: str, path: str) -> None:
        if isinstance(node, ScalarNode) and _expression(node.value):
            self.note(self.deferred, node, path, "A template expression requires Azure expansion")
            return
        if not isinstance(node, SequenceNode):
            self.note(self.issues, node, path, f"{kind} must be a sequence in the checked literal form")
            return
        self.sequences_checked += 1
        for index, item in enumerate(node.value):
            child = f"{path}[{index}]"
            if isinstance(item, ScalarNode) and _expression(item.value):
                self.note(self.deferred, item, child, "A template expression requires Azure expansion")
                continue
            if not isinstance(item, MappingNode):
                self.note(self.issues, item, child, f"A literal {kind} entry must be a mapping")
                continue
            self.entries_checked += 1
            deferred_before = len(self.deferred)
            fields = self.fields(item, child)
            if not fields and len(self.deferred) > deferred_before:
                continue
            if "template" in fields:
                self.note(self.deferred, fields["template"], child, "A template reference requires Azure expansion")
            elif kind == "steps":
                matches = STEP_TYPES.intersection(fields)
                if len(matches) != 1:
                    self.note(self.deferred, item, child, "The step type requires Azure validation")
            elif kind == "jobs":
                if "deployment" in fields or "job" not in fields:
                    self.note(self.deferred, item, child, "This job form requires Azure validation")
                else:
                    if "strategy" in fields:
                        self.note(self.deferred, fields["strategy"], child, "A job strategy requires Azure expansion")
                    if "steps" in fields:
                        self.sequence(fields["steps"], "steps", f"{child}.steps")
                    else:
                        self.note(self.deferred, item, child, "Job steps are not statically available")
            elif kind == "stages":
                if "stage" not in fields:
                    self.note(self.deferred, item, child, "This stage form requires Azure validation")
                elif "jobs" in fields:
                    self.sequence(fields["jobs"], "jobs", f"{child}.jobs")
                else:
                    self.note(self.deferred, item, child, "Stage jobs are not statically available")

    def scan(self, root: Node | None) -> dict[str, Any]:
        if not isinstance(root, MappingNode):
            return {"status": "invalid_input", "error": "The YAML root must be a mapping"}
        fields = self.fields(root, "$root")
        sections = [kind for kind in ("stages", "jobs", "steps") if kind in fields]
        if "extends" in fields:
            self.note(
                self.deferred, fields["extends"], "$root.extends", "An extended template requires Azure expansion"
            )
        if len(sections) > 1:
            self.note(self.deferred, root, "$root", "Multiple root sequence sections require Azure validation")
        for kind in sections:
            self.sequence(fields[kind], kind, f"$root.{kind}")
        if not sections and not self.deferred:
            self.note(self.deferred, root, "$root", "No supported sequence section was found")
        status = "issues" if self.issues else "indeterminate" if self.deferred else "no_shape_issues"
        return {
            "status": status,
            "sequences_checked": self.sequences_checked,
            "entries_checked": self.entries_checked,
            "issues": self.issues,
            "deferred": self.deferred,
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8-sig")
        result = ShapeScan().scan(yaml.compose(text, Loader=yaml.SafeLoader))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        result = {"status": "invalid_input", "error": str(exc)}
    result = {"kind": "azure_pipeline_sequence_shape_preflight", "azure_schema_validated": False, **result}
    if args.json:
        print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    else:
        print(f"Sequence-shape preflight: {result['status']}. This is not Azure schema validation.")
        for issue in result.get("issues", []) + result.get("deferred", []):
            print(f"{issue['path']}:{issue['line']}:{issue['column']}: {issue['message']}")
    return {"no_shape_issues": 0, "issues": 1, "indeterminate": 2, "invalid_input": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
