from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import crawl4ai_capture as capture
import crawl4ai_tool as launcher
import pytest


def test_isolated_cli_imports_trusted_tools_from_a_foreign_working_directory(tmp_path):
    (tmp_path / "prepare_crawl4ai_source.py").write_text("raise RuntimeError('untrusted import')\n", encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(tmp_path)}
    result = subprocess.run(
        [sys.executable, "-I", str(Path(launcher.__file__)), "--help"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=30,
        check=True,
    )
    assert result.returncode == 0 and b"{setup,check,crawl}" in result.stdout


@pytest.mark.parametrize("name", ["../../foreign.whl", "/foreign.whl", "C:\\foreign.whl"])
def test_receipt_cannot_select_a_wheel_outside_the_provider_home(tmp_path, monkeypatch, name):
    home = tmp_path / "provider"
    home.mkdir()
    (home / "installation.json").write_text(
        json.dumps({"schema_version": 1, "input_identity": "bound", "wheel_name": name, "provider_version": "test"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(launcher, "identity", lambda _root: "bound")
    touched = []
    monkeypatch.setattr(launcher.wheel, "prepare", lambda *args, **kwargs: touched.append(args))
    monkeypatch.setattr(launcher, "phase", lambda *args, **kwargs: {})
    with pytest.raises(ValueError, match="wheel"):
        launcher.verify(home)
    assert not touched


def test_profile_reparse_point_is_rejected_before_writing_to_it(tmp_path, monkeypatch):
    home = tmp_path / "provider"
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == home / "profile" or original(path))
    with pytest.raises(ValueError, match="linked"):
        launcher.environment(home)
    assert not (home / "profile").exists()


@pytest.mark.parametrize(
    "url",
    [
        "file:///packages/private",
        "http://files.pythonhosted.org/packages/provider.tar.gz",
        "ftp://files.pythonhosted.org/packages/provider.tar.gz",
        "https://foreign.example/packages/provider.tar.gz",
        "https://files.pythonhosted.org@foreign.example/packages/provider.tar.gz",
        "https://files.pythonhosted.org/not-an-artifact",
        "https://files.pythonhosted.org/packages/provider.tar.gz?alternate=1",
        "https://files.pythonhosted.org/packages/provider.tar.gz#alternate",
    ],
)
def test_source_download_rejects_non_artifact_urls_before_opening_a_connection(tmp_path, monkeypatch, url):
    contacted = []
    monkeypatch.setattr(launcher.http.client, "HTTPSConnection", lambda *args, **kwargs: contacted.append(args))
    with pytest.raises(ValueError, match="PyPI HTTPS artifact"):
        launcher.download_archive(tmp_path, {"archive_url": url})
    assert not contacted and not list(tmp_path.iterdir())


@pytest.mark.parametrize("status,body", [(200, b"source"), (302, b"source"), (403, b"denied"), (200, b"changed")])
def test_source_download_retains_denials_and_rejects_redirects_or_changed_bytes(tmp_path, monkeypatch, status, body):
    events: list[Any] = []
    response = SimpleNamespace(status=status, read=lambda limit: body[:limit])
    connection = SimpleNamespace(
        request=lambda *args, **kwargs: events.append((args, kwargs)),
        getresponse=lambda: response,
        close=lambda: events.append("closed"),
    )

    def connect(host, *, timeout):
        assert host == "files.pythonhosted.org" and timeout == 60
        return connection

    monkeypatch.setattr(launcher.http.client, "HTTPSConnection", connect)
    pin = {
        "archive_url": "https://files.pythonhosted.org/packages/provider.tar.gz",
        "archive_bytes": 6,
        "archive_sha256": hashlib.sha256(b"source").hexdigest(),
    }
    if status == 200 and body == b"source":
        assert launcher.download_archive(tmp_path, pin) == tmp_path / "upstream.tar.gz"
    else:
        with pytest.raises(ValueError):
            launcher.download_archive(tmp_path, pin)
    assert events == [
        (("GET", "/packages/provider.tar.gz"), {"headers": {"User-Agent": "AI-Skills-Provider-Setup/1"}}),
        "closed",
    ]
    native = json.loads((tmp_path / "upstream-response.json").read_bytes())
    assert native["url"] == pin["archive_url"] and native["status_code"] == status
    assert native["sha256"] == hashlib.sha256(body).hexdigest()
    assert (tmp_path / "upstream.tar.gz").read_bytes() == body


def test_source_download_closes_the_connection_after_a_transport_failure(tmp_path, monkeypatch):
    events = []

    def fail():
        raise launcher.http.client.RemoteDisconnected("fixture transport failure")

    connection = SimpleNamespace(
        request=lambda *args, **kwargs: None, getresponse=fail, close=lambda: events.append("closed")
    )
    monkeypatch.setattr(launcher.http.client, "HTTPSConnection", lambda *args, **kwargs: connection)
    with pytest.raises(launcher.http.client.RemoteDisconnected):
        launcher.download_archive(tmp_path, {"archive_url": "https://files.pythonhosted.org/packages/provider.tar.gz"})
    assert events == ["closed"] and not list(tmp_path.iterdir())


def test_provider_cache_identity_is_portable_and_detects_dependency_drift(tmp_path):
    names = ["source.json", "requirements.txt", "requirements-build.txt", "requirements-bootstrap.txt"]
    for name in names:
        target = tmp_path / "toolchains/crawl4ai" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = (launcher.ROOT / "toolchains/crawl4ai" / name).read_bytes().replace(b"\r\n", b"\n")
        target.write_bytes(raw.replace(b"\n", b"\r\n"))
    expected = launcher.identity(launcher.ROOT)
    assert launcher.identity(tmp_path) == expected
    (tmp_path / "unrelated-document.md").write_text("documentation change", encoding="utf-8")
    assert launcher.identity(tmp_path) == expected
    lock = tmp_path / "toolchains/crawl4ai/requirements.txt"
    lock.write_bytes(lock.read_bytes() + b"# changed dependency record\r\n")
    assert launcher.identity(tmp_path) != expected


@pytest.mark.parametrize("receipt", [None, [], {"schema_version": True}, {"schema_version": "1"}])
def test_malformed_installation_schema_is_rejected(tmp_path, receipt):
    home = tmp_path / "provider"
    home.mkdir()
    (home / "installation.json").write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        launcher.verify(home)


def test_failed_owned_phase_retains_native_output_and_cleanup_receipt(tmp_path, monkeypatch):
    def fail(*_args, **kwargs):
        kwargs["stdout"].write(b"native failure retained")
        return 124, {"active_processes_after_cleanup": 0, "termination_reason": "timeout"}

    monkeypatch.setattr(launcher.owned, "run_python", fail)
    home = tmp_path / "provider"
    with pytest.raises(ValueError, match="failed"):
        launcher.phase(home, "controlled-failure", ["unexecuted fixture"])
    receipts = list(home.glob("logs/*/process.json"))
    assert len(receipts) == 1
    recorded = json.loads(receipts[0].read_bytes())
    assert recorded["exit_code"] == 124 and recorded["termination_reason"] == "timeout"
    assert recorded["active_processes_after_cleanup"] == 0
    assert receipts[0].with_name("stdout.log").read_bytes() == b"native failure retained"


def test_provider_environment_does_not_inherit_external_provider_configuration(tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_SERVICE_TOKEN", "private-context")
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "foreign-provider"))
    monkeypatch.setenv("CRAWL4AI_BASE_DIRECTORY", str(tmp_path / "foreign-cache"))
    home = tmp_path / "provider"
    child = launcher.environment(home)
    assert "PRIVATE_SERVICE_TOKEN" not in child and "PYTHONPATH" not in child
    assert child["HOME"] == str(home / "profile")
    assert child["CRAWL4AI_BASE_DIRECTORY"] == str(home / "runtime-data")
    assert child["CRAWL4_AI_BASE_DIRECTORY"] == str(home / "setup-data")
    assert child["CRAWL4AI_CHROMIUM_SANDBOX"] == "true"
    assert not (tmp_path / "foreign-cache").exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://example.org",
        "file:///private",
        "https:///missing",
        "https://user:password@example.org",
        "https://@example.org",
    ],
)
def test_public_research_url_cannot_use_plaintext_local_files_or_credentials(url):
    with pytest.raises(ValueError, match="HTTPS"):
        capture.validate_url(url)


def test_invalid_target_does_not_create_provider_directories(tmp_path):
    with pytest.raises(ValueError, match="dedicated directory"):
        launcher.home_path(tmp_path, tmp_path / "unrelated-application")
    assert list(tmp_path.iterdir()) == []


def test_linked_installation_receipt_is_rejected_before_reading(tmp_path, monkeypatch):
    home = tmp_path / "provider"
    home.mkdir()
    receipt = home / "installation.json"
    receipt.write_text("private content must not be parsed", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path: path == receipt or original(path))
    with pytest.raises(ValueError, match="linked"):
        launcher.verify(home)


def test_native_denial_is_retained_without_claiming_source_review(tmp_path, monkeypatch):
    url = "https://example.org/denied"
    denied = {"url": url, "success": False, "status_code": 403, "error_message": "fixture denial", "markdown": None}

    async def operation(*_args):
        return denied, []

    monkeypatch.setattr(capture, "capture", operation)
    monkeypatch.setattr(capture, "admit_sources", lambda: {"version": "test", "runtime_files": []})
    monkeypatch.setenv("CRAWL4AI_CHROMIUM_SANDBOX", "true")
    output, metadata = tmp_path / "native.json", tmp_path / "metadata.json"
    status = capture.main(["--url", url, "--output", str(output), "--metadata", str(metadata), "--home", str(tmp_path)])
    assert status == 1 and json.loads(output.read_bytes()) == denied
    receipt = json.loads(metadata.read_bytes())
    assert not receipt["eligible_for_scope_review"] and not receipt["scope_reviewed"]
    assert receipt["native_result_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()


def test_source_admission_rejects_modified_or_external_provider_bytes(tmp_path, monkeypatch):
    source_path = tmp_path / "runtime/crawl4ai/fixture.py"
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"qualified provider source")
    pin = {
        "version": "test",
        "runtime_files": [
            {"path": "crawl4ai/fixture.py", "sha256": hashlib.sha256(source_path.read_bytes()).hexdigest()}
        ],
    }
    directory = tmp_path / "toolchains/crawl4ai"
    directory.mkdir(parents=True)
    (directory / "source.json").write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(capture, "ROOT", tmp_path)
    monkeypatch.setattr(capture.sys, "prefix", str(tmp_path / "runtime"))
    distribution = SimpleNamespace(version="test", locate_file=lambda _name: source_path)
    monkeypatch.setattr(capture.importlib.metadata, "distribution", lambda _name: distribution)
    assert capture.admit_sources() == pin
    source_path.write_bytes(b"changed source")
    with pytest.raises(ValueError, match="source differs"):
        capture.admit_sources()
    distribution.locate_file = lambda _name: tmp_path / "foreign-provider.py"
    with pytest.raises(ValueError, match="outside"):
        capture.admit_sources()


@pytest.mark.parametrize(
    "change", [None, "webdriver", "automation", "sandbox", "profile", "missing-browser", "plaintext-redirect"]
)
def test_live_browser_policy_rejects_hidden_automation_sandbox_bypass_and_foreign_profiles(
    tmp_path, monkeypatch, change
):
    home = tmp_path / "provider"
    settings = {}

    def configuration(**kwargs):
        settings.update(kwargs)
        return SimpleNamespace(**kwargs)

    class Page:
        url = "http://example.org" if change == "plaintext-redirect" else "https://example.org"

        @staticmethod
        async def evaluate(_expression):
            return change != "webdriver"

    class Crawler:
        hook: Any

        def __init__(self, **_kwargs):
            self.crawler_strategy = SimpleNamespace(set_hook=lambda _name, hook: setattr(self, "hook", hook))

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def arun(self, _url, **_kwargs):
            await self.hook(Page())
            return SimpleNamespace(model_dump=lambda **_kwargs: {"success": True})

    profile = tmp_path / "foreign" if change == "profile" else home / "temporary/profile"
    flags = ["chrome.exe", "--user-data-dir=" + str(profile)]
    if change == "automation":
        flags.append("--disable-blink-features=AutomationControlled")
    if change == "sandbox":
        flags.append("--no-sandbox")
    child = SimpleNamespace(name=lambda: "chrome.exe", cmdline=lambda: flags)
    process = SimpleNamespace(children=lambda **_kwargs: [] if change == "missing-browser" else [child])
    monkeypatch.setitem(
        sys.modules, "psutil", SimpleNamespace(Process=lambda: process, NoSuchProcess=ProcessLookupError)
    )
    monkeypatch.setitem(
        sys.modules,
        "crawl4ai",
        SimpleNamespace(
            AsyncWebCrawler=Crawler,
            BrowserConfig=configuration,
            CrawlerRunConfig=configuration,
            CacheMode=SimpleNamespace(BYPASS="bypass"),
        ),
    )
    operation = capture.capture("https://example.org", home)
    if change:
        with pytest.raises(ValueError):
            asyncio.run(operation)
    else:
        native, observations = asyncio.run(operation)
        assert native["success"] and observations[0]["navigator_webdriver"] is True
        assert observations[0]["browser_processes"] == 1 and observations[0]["forbidden_flags"] == []
    assert settings["enable_stealth"] is False and settings["ignore_https_errors"] is False
    assert settings["check_robots_txt"] is True and settings["max_retries"] == 0
    assert settings["fallback_fetch_function"] is None and settings["extraction_strategy"] is None
