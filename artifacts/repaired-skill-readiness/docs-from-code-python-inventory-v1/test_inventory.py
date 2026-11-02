from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(os.environ.get("DOCS_INVENTORY_SCRIPT", Path(__file__).with_name("inventory.py")))


def run(project: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(project), str(output)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )


def extract(tmp_path: Path, source: str) -> dict:
    project = tmp_path / "project with spaces"
    project.mkdir()
    (project / "app.py").write_text(source, encoding="utf-8")
    output = tmp_path / "out.json"
    result = run(project, output)
    assert result.returncode == 0, result.stderr
    return json.loads(output.read_text(encoding="utf-8"))


def test_flask_routes_do_not_include_cache_or_implicit_methods(tmp_path):
    result = extract(
        tmp_path,
        """
from flask import Flask
app = Flask(__name__)
cache = Cache()
@app.route("/users", methods=["GET", "POST"])
def users(): pass
@app.route("/health")
def health(): pass
@cache.get("/not-http")
def cached(): pass
""",
    )
    assert {(r["method"], r["path"]) for r in result["routes"]} == {
        ("GET", "/users"),
        ("POST", "/users"),
        ("GET", "/health"),
    }
    assert all(r["resolution"] == "direct" for r in result["routes"])
    assert result["kind"] == "static_candidates"
    assert result["limitations"] and ".venv" in result["skipped_directories"]


def test_fastapi_same_file_prefixes_and_multiple_mounts(tmp_path):
    result = extract(
        tmp_path,
        """
from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter(prefix="/v1")
@router.get("/users")
def users(): pass
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/internal")
""",
    )
    assert {(r["method"], r["path"]) for r in result["routes"]} == {
        ("GET", "/api/v1/users"),
        ("GET", "/internal/v1/users"),
    }
    assert all(r["resolution"] == "same_file_mount" for r in result["routes"])


def test_signature_preserves_defaults_kinds_and_return_annotation(tmp_path):
    source = 'def sample(name: str = "x", /, count: int = 1, *args: str, flag: bool = False, **kwargs: int) -> str:\n    return name\n'
    result = extract(tmp_path, source)
    actual = ast.parse(result["functions"][0]["signature"] + ":\n    pass\n").body[0]
    expected = ast.parse(source).body[0]
    assert isinstance(actual, ast.FunctionDef) and isinstance(expected, ast.FunctionDef)
    assert ast.dump(actual.args) == ast.dump(expected.args)
    assert ast.dump(actual.returns) == ast.dump(expected.returns)


def test_invalid_source_fails_without_creating_or_overwriting_output(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "broken.py").write_text("def broken(\n", encoding="utf-8")
    output = tmp_path / "output.json"
    result = run(project, output)
    assert result.returncode != 0
    assert not output.exists()
    output.write_text("existing", encoding="utf-8")
    result = run(project, output)
    assert result.returncode != 0
    assert output.read_text(encoding="utf-8") == "existing"


@pytest.mark.parametrize(
    "source",
    [
        'from fastapi import APIRouter\nr = APIRouter(prefix="/x")\n@r.get("/users")\ndef f(): pass\n',
        'from fastapi import APIRouter, FastAPI\na = FastAPI()\nr = APIRouter(prefix=prefix())\n@r.get("/users")\ndef f(): pass\na.include_router(r, prefix="/api")\n',
        'from fastapi import APIRouter, FastAPI\na = FastAPI()\nr = APIRouter(prefix="/v1")\n@r.get("/users")\ndef f(): pass\na.include_router(r, prefix=prefix())\n',
        'from fastapi import APIRouter, FastAPI\na = FastAPI()\nr = APIRouter(prefix="/v1")\na.include_router(r, prefix="/api")\n@r.get("/users")\ndef f(): pass\n',
    ],
    ids=["unmounted", "dynamic-router-prefix", "dynamic-mount-prefix", "early-mount"],
)
def test_unresolved_mounts_are_not_presented_as_final_paths(tmp_path, source):
    result = extract(tmp_path, source)
    assert len(result["routes"]) == 1
    assert result["routes"][0]["local_path"] == "/users"
    assert result["routes"][0]["path"] is None
    assert result["routes"][0]["resolution"] == "unresolved"


def test_aliases_dynamic_paths_and_dynamic_methods_are_not_guessed(tmp_path):
    result = extract(
        tmp_path,
        """
import flask as fl
from fastapi import FastAPI as API
web = fl.Flask(__name__)
api = API()
@web.route(path(), methods=methods())
def dynamic(): pass
@api.get(path="/known")
async def known(): pass
""",
    )
    assert {(r["method"], r["path"]) for r in result["routes"]} == {
        (None, None),
        ("GET", "/known"),
    }
    assert result["functions"][1]["signature"] == "async def known()"


def test_rebinding_does_not_make_unrelated_decorator_a_route(tmp_path):
    result = extract(
        tmp_path,
        """
from fastapi import FastAPI
app = FastAPI()
app = cache
@app.get("/cached")
def handler(): pass
""",
    )
    assert result["routes"] == []


@pytest.mark.parametrize(
    "mutation",
    [
        "if choice:\n    app = cache",
        "class app: pass",
        "set_value(app := cache)",
        "from unknown_package import *",
    ],
    ids=["conditional-assignment", "class-rebind", "named-expression", "star-import"],
)
def test_conditional_or_other_uncertain_rebinding_is_not_assumed(tmp_path, mutation):
    source = f'from fastapi import FastAPI\napp = FastAPI()\n{mutation}\n@app.get("/x")\ndef handler(): pass\n'
    assert extract(tmp_path, source)["routes"] == []


def test_keyword_expansion_does_not_invent_methods_or_prefixes(tmp_path):
    result = extract(
        tmp_path,
        """
from flask import Flask
from fastapi import APIRouter, FastAPI
web = Flask(__name__)
app = FastAPI()
router = APIRouter(**options)
@web.route("/x", **options)
def flask_handler(): pass
@router.get("/items")
def fast_handler(): pass
app.include_router(router, prefix="/api")
""",
    )
    first, second = result["routes"]
    assert first["method"] is None and first["path"] == "/x"
    assert second["method"] == "GET" and second["path"] is None
    assert second["resolution"] == "unresolved"


def test_aliasing_router_preserves_identity_across_mount(tmp_path):
    result = extract(
        tmp_path,
        """
from fastapi import APIRouter, FastAPI
app = FastAPI()
router = APIRouter(prefix="/v1")
alias = router
@alias.get("/items")
def items(): pass
app.include_router(router, prefix="/api")
""",
    )
    assert [route["path"] for route in result["routes"]] == ["/api/v1/items"]


def test_selected_candidates_agree_with_real_framework_route_tables(tmp_path):
    source = """
from flask import Flask
from fastapi import APIRouter, FastAPI
web = Flask(__name__)
api = FastAPI()
router = APIRouter(prefix="/v1")
@web.route("/health", methods=["GET", "POST"])
def health(): return "ok"
@router.get("/items")
def items(): return []
api.include_router(router, prefix="/api")
"""
    data = extract(tmp_path, source)
    # Only this owned fixture is executed. The inventory itself parses source.
    runtime = runpy.run_path(str(tmp_path / "project with spaces" / "app.py"))
    flask_rules = {
        (method, rule.rule)
        for rule in runtime["web"].url_map.iter_rules()
        if rule.endpoint == "health"
        for method in rule.methods
    }
    fastapi_rules = {
        (method.upper(), path)
        for path, operations in runtime["api"].openapi()["paths"].items()
        for method in operations
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"}
    }
    candidates = {(row["method"], row["path"]) for row in data["routes"]}
    assert candidates == {
        ("GET", "/health"),
        ("POST", "/health"),
        ("GET", "/api/v1/items"),
    }
    assert candidates <= flask_rules | fastapi_rules
    assert ("HEAD", "/health") in flask_rules and ("OPTIONS", "/health") in flask_rules


def test_prior_independent_five_case_controls(tmp_path):
    root = Path(__file__).resolve().parents[3]
    source = root / "benchmarks/dependency-regressions"
    fixture_path = tmp_path / "fixture.py"
    shutil.copyfile(source / "docs_from_code_fixture.py", fixture_path)
    shutil.copyfile(SCRIPT, tmp_path / "original.py")

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load the independent control")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    fixture = load("independent_docs_fixture", fixture_path)
    controls = load("independent_docs_controls", source / "docs_from_code_controls.py")
    assert all(controls.assess(fixture.run(None)).values())


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python syntax requires 3.12")
def test_generic_type_parameters_are_retained(tmp_path):
    source = "def first[T](values: list[T]) -> T:\n    return values[0]\n"
    result = extract(tmp_path, source)
    actual = ast.parse(result["functions"][0]["signature"] + ":\n    pass\n").body[0]
    expected = ast.parse(source).body[0]
    assert ast.dump(actual.type_params[0]) == ast.dump(expected.type_params[0])
    assert ast.dump(actual.args) == ast.dump(expected.args)


def test_unrecognized_imports_and_nested_definitions_do_not_become_routes(tmp_path):
    result = extract(
        tmp_path,
        """
from something_else import FastAPI
app = FastAPI()
@app.get("/not-http")
def handler(): pass
def outer():
    @app.get("/nested")
    def nested(): pass
""",
    )
    assert result["routes"] == []
    assert {f["name"] for f in result["functions"]} == {"handler", "outer"}


def test_source_is_parsed_not_executed(tmp_path):
    result = extract(
        tmp_path,
        'from pathlib import Path\nPath("executed").touch()\ndef api(): pass\n',
    )
    assert len(result["functions"]) == 1
    assert not (tmp_path / "project with spaces" / "executed").exists()


def test_declared_python_source_encoding_and_hash_are_respected(tmp_path):
    project = tmp_path / "encoded"
    project.mkdir()
    raw = b'# coding: latin-1\ndef title():\n    """caf\xe9"""\n'
    (project / "app.py").write_bytes(raw)
    output = tmp_path / "result.json"
    result = run(project, output)
    assert result.returncode == 0, result.stderr
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["files"] == [{"file": "app.py", "sha256": hashlib.sha256(raw).hexdigest()}]
    assert data["functions"][0]["docstring"] == "café"


def test_missing_or_non_directory_root_is_an_error(tmp_path):
    output = tmp_path / "result.json"
    assert run(tmp_path / "missing", output).returncode != 0
    path = tmp_path / "single.py"
    path.write_text("", encoding="utf-8")
    assert run(path, output).returncode != 0
    assert not output.exists()


def test_output_cannot_overwrite_an_inventoried_source(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    source = project / "app.py"
    source.write_text("def example(): pass\n", encoding="utf-8")
    result = run(project, source)
    assert result.returncode != 0
    assert source.read_text(encoding="utf-8") == "def example(): pass\n"
    new_source = project / "generated.py"
    assert run(project, new_source).returncode != 0
    assert not new_source.exists()


def test_existing_output_is_replaced_only_after_successful_analysis(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("def example(): pass\n", encoding="utf-8")
    output = tmp_path / "out.json"
    output.write_text("old", encoding="utf-8")
    result = run(project, output)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text(encoding="utf-8"))["functions"][0]["name"] == "example"
    assert list(tmp_path.glob(".python-inventory-*")) == []
