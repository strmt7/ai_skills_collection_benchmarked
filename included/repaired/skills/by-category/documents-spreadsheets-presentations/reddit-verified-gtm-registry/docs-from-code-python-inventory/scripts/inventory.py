"""Inventory source-level Python functions and selected HTTP route candidates."""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import sys
import tempfile
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Any

METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"})
SKIP = frozenset({".git", ".venv", "venv", "node_modules", "__pycache__"})


@dataclass(eq=False)
class Receiver:
    framework: str
    kind: str
    prefix: str | None


def literal(node: ast.AST | None) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def keyword(call: ast.Call, name: str) -> ast.AST | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def configured_prefix(call: ast.Call) -> str | None:
    value = keyword(call, "prefix")
    if value is not None:
        return literal(value)
    return None if any(item.arg is None for item in call.keywords) else ""


def methods(call: ast.Call, name: str) -> list[str | None]:
    if name.upper() in METHODS:
        return [name.upper()]
    node = keyword(call, "methods")
    if node is None:
        return ["GET"] if name == "route" and not any(item.arg is None for item in call.keywords) else [None]
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return [None]
    values = [literal(element) for element in node.elts]
    if not values or any(value is None or value.upper() not in METHODS for value in values):
        return [None]
    return list(dict.fromkeys(value.upper() for value in values if value is not None))


def inspect_module(tree: ast.Module, path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    modules: dict[str, str] = {}
    constructors: dict[str, tuple[str, str]] = {}
    bindings: dict[str, Receiver] = {}
    functions: list[dict[str, Any]] = []
    pending: list[tuple[Receiver, dict[str, Any]]] = []
    mounts: list[tuple[Receiver, str | None, int]] = []
    supported = {
        ("fastapi", "FastAPI"): "app",
        ("fastapi", "APIRouter"): "router",
        ("flask", "Flask"): "app",
    }

    def forget(name: str) -> None:
        modules.pop(name, None)
        constructors.pop(name, None)
        bindings.pop(name, None)

    def forget_import(alias: ast.alias) -> None:
        if alias.name == "*":
            modules.clear()
            constructors.clear()
            bindings.clear()
        else:
            forget(alias.asname or alias.name.split(".")[0])

    def forget_uncertain_writes(node: ast.AST) -> None:
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                forget(child.id)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                forget(child.name)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                for alias in child.names:
                    forget_import(alias)

    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                forget(name)
                if alias.name in {"fastapi", "flask"}:
                    modules[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                name = alias.asname or alias.name
                forget_import(alias)
                kind = supported.get((node.module, alias.name)) if node.module is not None else None
                if node.module is not None and kind is not None:
                    constructors[name] = (node.module, kind)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = node.value
            resolved: Receiver | None = None
            if isinstance(value, ast.Name):
                resolved = bindings.get(value.id)
            elif isinstance(value, ast.Call):
                factory = value.func
                if isinstance(factory, ast.Name):
                    info = constructors.get(factory.id)
                elif isinstance(factory, ast.Attribute) and isinstance(factory.value, ast.Name):
                    framework = modules.get(factory.value.id)
                    kind = supported.get((framework, factory.attr)) if framework is not None else None
                    info = (framework, kind) if framework is not None and kind is not None else None
                else:
                    info = None
                if info:
                    resolved = Receiver(
                        info[0],
                        info[1],
                        configured_prefix(value) if info[1] == "router" else "",
                    )
            for target in targets:
                if isinstance(target, ast.Name):
                    forget(target.id)
                    if resolved is not None:
                        bindings[target.id] = resolved
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            type_params = getattr(node, "type_params", ())
            generic = f"[{', '.join(ast.unparse(item) for item in type_params)}]" if type_params else ""
            signature = f"{'async ' if isinstance(node, ast.AsyncFunctionDef) else ''}def {node.name}{generic}({ast.unparse(node.args)})"
            if node.returns is not None:
                signature += f" -> {ast.unparse(node.returns)}"
            functions.append(
                {
                    "name": node.name,
                    "signature": signature,
                    "docstring": ast.get_docstring(node),
                    "file": path,
                    "line": node.lineno,
                }
            )
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                if not isinstance(decorator.func.value, ast.Name):
                    continue
                receiver_name = decorator.func.value.id
                receiver = bindings.get(receiver_name)
                name = decorator.func.attr
                if receiver is None or (name.upper() not in METHODS and name not in {"route", "api_route"}):
                    continue
                if name == "route" and receiver.framework != "flask":
                    continue
                if name == "api_route" and receiver.framework != "fastapi":
                    continue
                route_value = (
                    decorator.args[0]
                    if decorator.args
                    else keyword(decorator, "rule" if receiver.framework == "flask" else "path")
                )
                local_path = literal(route_value)
                for method in methods(decorator, name):
                    pending.append(
                        (
                            receiver,
                            {
                                "framework": receiver.framework,
                                "receiver": receiver_name,
                                "handler": node.name,
                                "method": method,
                                "local_path": local_path,
                                "file": path,
                                "line": decorator.lineno,
                            },
                        )
                    )
            forget(node.name)
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            forget_uncertain_writes(node)
            call = node.value
            if not isinstance(call.func, ast.Attribute) or call.func.attr != "include_router":
                continue
            if not isinstance(call.func.value, ast.Name) or not call.args or not isinstance(call.args[0], ast.Name):
                continue
            parent, child = (
                bindings.get(call.func.value.id),
                bindings.get(call.args[0].id),
            )
            if (
                parent
                and child
                and parent.framework == child.framework == "fastapi"
                and parent.kind == "app"
                and child.kind == "router"
            ):
                mounts.append((child, configured_prefix(call), node.lineno))
        else:
            forget_uncertain_writes(node)
    routes: list[dict[str, Any]] = []
    for receiver, route in pending:
        local = route["local_path"]
        if receiver.kind == "app":
            routes.append(
                {
                    **route,
                    "path": local,
                    "resolution": "direct" if local is not None else "unresolved",
                }
            )
            continue
        matches = [(prefix, line) for child, prefix, line in mounts if child is receiver and line > route["line"]]
        if not matches:
            routes.append({**route, "path": None, "resolution": "unresolved"})
        for mount_prefix, line in matches:
            path_value = (
                mount_prefix + receiver.prefix + local
                if mount_prefix is not None and receiver.prefix is not None and local is not None
                else None
            )
            routes.append(
                {
                    **route,
                    "path": path_value,
                    "resolution": "same_file_mount" if path_value is not None else "unresolved",
                    "mount_line": line,
                }
            )
    return functions, routes


def inventory(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("project root must be a directory")
    files: list[dict[str, str]] = []
    functions: list[dict[str, Any]] = []
    routes: list[dict[str, Any]] = []

    def failed(error: OSError) -> None:
        raise error

    for directory, dirs, names in os.walk(root, followlinks=False, onerror=failed):
        dirs[:] = sorted(name for name in dirs if name not in SKIP)
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            file = Path(directory) / name
            relative = file.relative_to(root).as_posix()
            content = file.read_bytes()
            encoding, _ = tokenize.detect_encoding(io.BytesIO(content).readline)
            tree = ast.parse(content.decode(encoding), filename=relative)
            found_functions, found_routes = inspect_module(tree, relative)
            files.append({"file": relative, "sha256": hashlib.sha256(content).hexdigest()})
            functions.extend(found_functions)
            routes.extend(found_routes)
    return {
        "schema_version": 1,
        "kind": "static_candidates",
        "limitations": [
            "Top-level functions and selected directly constructed Flask or FastAPI objects only.",
            "Same-file direct FastAPI router inclusions only; dynamic and cross-file mounts may be unresolved.",
            "Reported methods are explicitly declared or Flask's default GET; implicit methods are not enumerated.",
            "Static candidates require source and runtime verification and are not a complete API contract.",
        ],
        "skipped_directories": sorted(SKIP),
        "files": files,
        "functions": functions,
        "routes": routes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = inventory(args.project_root)
        output = args.output.resolve()
        root = args.project_root.resolve(strict=True)
        if (output.suffix == ".py" and output.is_relative_to(root)) or any(
            (root / item["file"]).resolve() == output for item in result["files"]
        ):
            raise ValueError("output must not be a Python source file inside the project")
        data = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        descriptor, name = tempfile.mkstemp(prefix=".python-inventory-", dir=output.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(data)
            os.replace(temporary, output)
        finally:
            if temporary.exists():
                temporary.unlink()
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        print(f"Inventory failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
