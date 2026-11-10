"""Check an explicitly owned package graph without modifying its interpreter."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import re
import struct
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--requirements", type=Path, action="append", default=[])
    parser.add_argument("--import", dest="imports", action="append", default=[])
    return parser


def observation(packages: Path, requirements: list[Path], imports: list[str]) -> dict[str, object]:
    sys.path.insert(0, str(packages))
    versions: dict[str, str] = {}
    distributions = list(importlib.metadata.distributions(path=[str(packages)]))
    for distribution in distributions:
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        if name in versions:
            raise ValueError(f"Duplicate installed distribution: {name}")
        versions[name] = distribution.version
    expected: dict[str, str] = {}
    if requirements:
        from packaging.requirements import Requirement
        from packaging.utils import canonicalize_name

        for path in requirements:
            statements = path.read_text(encoding="utf-8").replace("\\\n", " ").splitlines()
            for statement in statements:
                statement = statement.split("#", 1)[0].strip()
                if not statement:
                    continue
                requirement = Requirement(statement.split("--hash=", 1)[0].strip())
                if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                    continue
                pins = list(requirement.specifier)
                if requirement.url or len(pins) != 1 or pins[0].operator != "==" or "*" in pins[0].version:
                    raise ValueError("Bootstrap graphs require exact registry version pins")
                name = canonicalize_name(requirement.name)
                version = pins[0].version
                if name in expected and expected[name] != version:
                    raise ValueError(f"Conflicting locked distribution: {name}")
                expected[name] = version
        if versions != expected:
            raise ValueError("Installed distribution inventory differs from the selected complete locks")
        for distribution in distributions:
            for dependency in distribution.requires or []:
                requirement = Requirement(dependency)
                if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                    continue
                dependency_version = versions.get(canonicalize_name(requirement.name))
                if dependency_version is None or not requirement.specifier.contains(dependency_version):
                    raise ValueError(f"Unsatisfied installed dependency: {requirement.name}")
    elif versions:
        raise ValueError("A standard-library profile contains undeclared packages")
    for name in imports:
        importlib.import_module(name)
    return {
        "python": platform.python_version(),
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "implementation": sys.implementation.name,
        "bits": struct.calcsize("P") * 8,
        "isolated": sys.flags.isolated,
        "no_user_site": sys.flags.no_user_site,
        "packages": sorted(versions.items()),
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(observation(args.packages, args.requirements, args.imports), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
