from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any

import prepare_crawl4ai_source as source
import pytest
import verify_crawl4ai_wheel as wheel
from check_crawl4ai_contracts import error_chain


def archive(entries):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as output:
        for name, data in entries:
            member = tarfile.TarInfo(name)
            if data is None:
                member.type, member.linkname = tarfile.SYMTYPE, "../outside"
                output.addfile(member)
            else:
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
    raw = stream.getvalue()
    pin = {
        "archive_bytes": len(raw),
        "archive_sha256": source.digest(raw),
        "archive_members": len(entries),
        "archive_root": "crawl4ai-0.9.5",
        "source_files": len(entries),
        "unpacked_bytes": sum(len(data or b"") for _, data in entries),
    }
    return raw, pin


def test_archive_exact_bytes_and_regular_files():
    raw, pin = archive([("crawl4ai-0.9.5/plain.py", b"exact\r\n")])
    assert source.archive_files(raw, pin) == {"plain.py": b"exact\r\n"}
    with pytest.raises(ValueError, match="pinned bytes"):
        source.archive_files(raw + b"changed", pin)


@pytest.mark.parametrize(
    "entries",
    [
        [("../outside", b"outside")],
        [("/outside", b"outside")],
        [("other-root/file", b"outside")],
        [("crawl4ai-0.9.5/../outside", b"outside")],
        [("crawl4ai-0.9.5/link", None)],
        [("crawl4ai-0.9.5/a", b"one"), ("crawl4ai-0.9.5/a", b"two")],
    ],
)
def test_archive_rejects_external_special_and_duplicate_members(entries):
    raw, pin = archive(entries)
    with pytest.raises(ValueError):
        source.archive_files(raw, pin)


@pytest.fixture
def adaptation():
    return {
        "crawl4ai/async_crawler_strategy.py": b'def opening(path, flags):\n    return os.open(path, flags | os.O_NOFOLLOW)\ndef filename(filename):\n    safe_name = os.path.basename(filename or "")\n    return safe_name\n',
        "crawl4ai/models.py": b'class CrawlResult:\n    fit_html: str | None = None\n    kept = "preserve"\n    @property\n    def fit_html(self):\n        raise RuntimeError("conflicting")\n    def after(self):\n        return self.kept\n',
        "crawl4ai/browser_manager.py": b'class Browser:\n    def managed(config):\n        flags = [\n            "--disable-blink-features=AutomationControlled",\n        ]\n        # GPU flags disable WebGL which anti-bot sensors detect as headless.\n        return flags\n    def ordinary(self):\n        args = [\n            "--disable-blink-features=AutomationControlled",\n        ]\n        if self.config.memory_saving_mode:\n            args.append("kept")\n        return args\n',
        "crawl4ai/__version__.py": b'__version__ = "0.9.5"\n',
        "pyproject.toml": b'license = "Apache-2.0"\n',
        "untouched": b"immutable\r\n",
    }


def test_repairs_preserve_data_field_unrelated_bytes_and_explicit_modes(adaptation):
    import ast
    from types import SimpleNamespace

    before = adaptation.copy()
    result = source.adapt(adaptation, b"licensed source", b"full notice", "0.9.5+catalog.portable3")
    assert adaptation == before and result["untouched"] == before["untouched"]
    namespace: dict[str, Any] = {}
    exec(compile(ast.parse(result["crawl4ai/models.py"]), "fixture", "exec"), namespace)
    model = namespace["CrawlResult"]()
    assert model.fit_html is None and model.after() == "preserve"
    namespace = {}
    exec(compile(ast.parse(result["crawl4ai/browser_manager.py"]), "fixture", "exec"), namespace)
    browser = namespace["Browser"]
    for mode in (False, True):
        configuration = SimpleNamespace(enable_stealth=mode, memory_saving_mode=False)
        instance = browser()
        instance.config = configuration
        assert bool(browser.managed(configuration)) is mode
        assert bool(instance.ordinary()) is mode
    assert result["crawl4ai/catalog_download.py"] == b"licensed source"
    assert result["CATALOG_BUILD_NOTICE.txt"] == b"full notice"


@pytest.mark.parametrize(
    "name",
    [
        "crawl4ai/async_crawler_strategy.py",
        "crawl4ai/models.py",
        "crawl4ai/browser_manager.py",
        "crawl4ai/__version__.py",
        "pyproject.toml",
    ],
)
def test_source_anchor_drift_is_an_error(adaptation, name):
    adaptation[name] = b"changed source"
    with pytest.raises((ValueError, SyntaxError)):
        source.adapt(adaptation, b"vendor", b"notice", "identified")


def test_stage_never_overwrites_and_check_is_strict(tmp_path, monkeypatch):
    monkeypatch.setattr(
        source,
        "inputs",
        lambda *_: (
            {"version": "test", "archive_sha256": "a" * 64, "source_date_epoch": 1},
            {"exact.py": b"source\r\n"},
        ),
    )
    target = tmp_path / ".venv/stage"
    source.prepare(tmp_path, Path("unused"), target)
    assert source.prepare(tmp_path, Path("unused"), target, check=True)["ok"]
    with pytest.raises(ValueError, match="already exists"):
        source.prepare(tmp_path, Path("unused"), target)
    (target / "node_modules").mkdir()
    (target / "node_modules/extra.py").write_text("unexpected source")
    with pytest.raises(ValueError, match="differs"):
        source.prepare(tmp_path, Path("unused"), target, check=True)
    assert (target / "exact.py").read_bytes() == b"source\r\n"


@pytest.mark.parametrize("destination", ["included/skills/source", "toolchains/crawl4ai", ".venv", "../outside"])
def test_source_stage_cannot_overlap_repository_inputs(tmp_path, destination):
    with pytest.raises(ValueError, match="workspace .venv"):
        source.prepare(tmp_path, Path("unused"), tmp_path / destination)


def test_wheel_lock_substitution_retains_every_dependency(tmp_path):
    import zipfile

    directory = tmp_path / source.INPUTS
    (directory / "vendor").mkdir(parents=True)
    (directory / "vendor/LICENSE").write_bytes(b"full license")
    (directory / "CATALOG_BUILD_NOTICE.txt").write_bytes(b"full notice")
    (directory / "requirements.txt").write_text(
        "other==1.2 --hash=sha256:" + "b" * 64 + "\nCrawl4AI==0.9.5 --hash=sha256:" + "a" * 64 + "\n"
    )
    package = tmp_path / "fixture.whl"
    with zipfile.ZipFile(package, "w") as output:
        output.writestr("crawl4ai/source.py", b"source")
        output.writestr("fixture.dist-info/licenses/LICENSE", b"full license")
        output.writestr("fixture.dist-info/licenses/CATALOG_BUILD_NOTICE.txt", b"full notice")
    pin = {
        "version": "0.9.5+catalog.portable3",
        "qualified_wheel_sha256": source.digest(package.read_bytes()),
        "runtime_files": [{"path": "crawl4ai/source.py", "sha256": source.digest(b"source")}],
    }
    (directory / "source.json").write_text(json.dumps(pin))
    _, lock = wheel.verify_wheel(tmp_path, package)
    assert lock.splitlines()[0] == (directory / "requirements.txt").read_bytes().splitlines()[0]
    assert b"Crawl4AI==0.9.5+catalog.portable3" in lock
    target = tmp_path / ".venv/admission"
    assert wheel.prepare(tmp_path, package, target)["ok"]
    assert wheel.prepare(tmp_path, package, target, check=True)["ok"]
    with pytest.raises(ValueError, match="already exists"):
        wheel.prepare(tmp_path, package, target)
    package.write_bytes(package.read_bytes() + b"alteration")
    with pytest.raises(ValueError, match="qualified reproducible"):
        wheel.verify_wheel(tmp_path, package)


def test_cli_errors_are_json_not_false_success(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(source, "ROOT", tmp_path)
    assert (
        source.main(["--archive", str(tmp_path / "missing"), "--stage", str(tmp_path / ".venv/stage"), "--json"]) == 1
    )
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_native_rejection_evidence_keeps_root_cause_and_terminates_cycles():
    original = ValueError("reserved destination")
    wrapped = RuntimeError("HTTP request failed")
    wrapped.__context__ = original
    assert error_chain(wrapped) == [wrapped, original]
    original.__context__ = wrapped
    assert error_chain(wrapped) == [wrapped, original]


def test_installed_admission_rejects_changed_external_and_wrong_version_sources(tmp_path, monkeypatch):
    from types import SimpleNamespace

    prefix = tmp_path / "runtime"
    prefix.mkdir()
    installed = prefix / "source.py"
    installed.write_bytes(b"admitted source")
    pin = {
        "version": "identified",
        "runtime_files": [{"path": "crawl4ai/source.py", "sha256": source.digest(installed.read_bytes())}],
    }
    distribution = SimpleNamespace(version="identified", locate_file=lambda _: installed)
    monkeypatch.setattr(wheel.sys, "prefix", str(prefix))
    monkeypatch.setattr(wheel.importlib.metadata, "distribution", lambda _: distribution)
    assert wheel.installed_files(pin) == 1
    installed.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source differs"):
        wheel.installed_files(pin)
    installed.write_bytes(b"admitted source")
    distribution.locate_file = lambda _: tmp_path / "outside.py"
    with pytest.raises(ValueError, match="source differs"):
        wheel.installed_files(pin)
    distribution.version = "wrong"
    with pytest.raises(ValueError, match="version differs"):
        wheel.installed_files(pin)


def test_native_evidence_is_exclusive_and_retains_execution_failure(tmp_path, monkeypatch):
    import check_crawl4ai_contracts as controls

    def fail(_fixture):
        raise RuntimeError("native provider failed")

    monkeypatch.setattr(controls, "run", fail)
    output = tmp_path / "receipt.json"
    arguments = ["--fixture-root", str(tmp_path / "fixture"), "--output", str(output)]
    assert controls.main(arguments) == 1
    assert json.loads(output.read_bytes())["errors"] == [
        {"error_type": "RuntimeError", "error": "native provider failed"}
    ]
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        controls.main(arguments)
    assert output.read_bytes() == before


def test_runtime_inventory_rejects_duplicate_files():
    with pytest.raises(ValueError, match="unique files"):
        source.runtime_sources(
            {"runtime_files": [{"path": "source.py", "sha256": "a"}, {"path": "source.py", "sha256": "b"}]}
        )
