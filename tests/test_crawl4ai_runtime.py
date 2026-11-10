"""Independent full browser-payload admission and runtime ownership contracts."""

from __future__ import annotations

import hashlib
import json

import crawl4ai_runtime as runtime
import pytest


@pytest.fixture
def browser(tmp_path, monkeypatch):
    root = tmp_path / "checkout"
    directory = root / "toolchains/crawl4ai"
    directory.mkdir(parents=True)
    home = tmp_path / "owned"
    payload = home / "browsers/qualified/browser.bin"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"independent browser payload")
    pin = {
        "driver": "playwright",
        "driver_version": "1.65.0",
        "chromium_version": "test",
        "directories": {"qualified": ["INSTALLATION_COMPLETE"]},
        "files": [
            {
                "path": "qualified/browser.bin",
                "bytes": payload.stat().st_size,
                "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
            }
        ],
    }
    (directory / "browser.json").write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(runtime, "ROOT", root)
    monkeypatch.setattr(runtime.importlib.metadata, "version", lambda _: "1.65.0")
    return home, payload


def test_complete_browser_payload_is_admitted(browser):
    home, _ = browser
    assert runtime.check_browser(home)["browser_files_admitted"] == 1


@pytest.mark.parametrize("change", ["missing", "modified", "extra", "marker", "driver"])
def test_browser_admission_rejects_payload_drift_before_launch(browser, monkeypatch, change):
    home, payload = browser
    if change == "missing":
        payload.unlink()
    elif change == "modified":
        payload.write_bytes(b"different browser payload")
    elif change == "extra":
        (payload.parent / "unadmitted.dll").write_bytes(b"extra")
    elif change == "marker":
        (payload.parent / "INSTALLATION_COMPLETE").write_bytes(b"not an empty native marker")
    else:
        monkeypatch.setattr(runtime.importlib.metadata, "version", lambda _: "unqualified")
    with pytest.raises(ValueError):
        runtime.check_browser(home)


def test_runtime_ownership_is_checked_before_provider_import(tmp_path, monkeypatch):
    touched = []
    monkeypatch.setattr(runtime.wheel, "installed_files", lambda _: touched.append(True))
    with pytest.raises(ValueError, match="owned crawler runtime"):
        runtime.check_runtime(tmp_path)
    assert not touched
