"""Independent automatic-setup recovery and ownership contracts."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

import _provider_launch as launch
import pytest


@pytest.fixture
def installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    root = tmp_path / "checkout"
    root.mkdir()
    events: list[tuple[str, Path]] = []

    def setup(home: Path):
        events.append(("setup", home))
        home.mkdir()
        (home / "package.txt").write_text("qualified", encoding="utf-8")
        return {"ok": True, "home": str(home)}

    def verify(home: Path):
        events.append(("verify", home))
        if not (home / "package.txt").is_file():
            raise ValueError("Missing required distribution")
        return {"ok": True, "home": str(home)}

    monkeypatch.setattr(launch, "identity", lambda _, name="cocoindex": "a" * 64)
    monkeypatch.setattr(launch, "exclusive", lambda _: contextlib.nullcontext())
    monkeypatch.setattr(launch.provider, "setup", setup)
    monkeypatch.setattr(launch.provider, "verify", verify)
    return root, root / ".venv/agent-tools/automatic-cocoindex", events


def test_missing_provider_installs_once_and_admitted_provider_is_reused(installation):
    root, base, events = installation
    first, installed = launch.prepare(root)
    second, reused = launch.prepare(root)
    assert first == second and first.is_relative_to(base)
    assert [kind for kind, _ in events] == ["setup", "verify"]
    assert installed["automatic_setup"]["newly_installed"] is True
    assert reused["automatic_setup"]["newly_installed"] is False


def test_missing_distribution_recovers_in_a_new_profile_and_preserves_failed_profile(installation):
    root, base, events = installation
    first, _ = launch.prepare(root)
    (first / "package.txt").unlink()
    (first / "evidence.txt").write_bytes(b"preserve diagnostics")
    second, result = launch.prepare(root)
    assert second != first and (second / "package.txt").is_file()
    assert (first / "evidence.txt").read_bytes() == b"preserve diagnostics"
    assert result["automatic_setup"]["recovered_previous_profile"] is True
    assert len(list(base.glob("logs/*/rejected-profile.json"))) == 1
    assert [kind for kind, _ in events] == ["setup", "verify", "setup"]


@pytest.mark.parametrize("raw", [b"\xffnot UTF-8", b"{broken", b"[]", b"null"])
def test_malformed_pointer_is_retained_and_recovered_without_adopting_its_contents(installation, raw):
    root, base, _ = installation
    first, _ = launch.prepare(root)
    pointer = next(base.glob("active-*.json"))
    pointer.write_bytes(raw)
    second, result = launch.prepare(root)
    assert first != second and first.is_dir()
    assert result["automatic_setup"]["recovered_previous_profile"] is True
    assert next(base.glob("logs/*/rejected-pointer.native")).read_bytes() == raw


@pytest.mark.parametrize("profile", ["../../outside", "profile-" + "a" * 13, "profile-" + "A" * 12, 42])
def test_pointer_cannot_select_an_external_or_noncanonical_profile(installation, profile):
    root, base, events = installation
    first, _ = launch.prepare(root)
    pointer = next(base.glob("active-*.json"))
    receipt = json.loads(pointer.read_bytes())
    receipt["profile"] = profile
    pointer.write_text(json.dumps(receipt), encoding="utf-8")
    second, _ = launch.prepare(root)
    assert first != second
    assert all(home.is_relative_to(base) for _, home in events)


def test_existing_unowned_cache_is_untouched(installation):
    root, base, events = installation
    base.mkdir(parents=True)
    (base / "canary").write_bytes(b"unrelated data")
    with pytest.raises(ValueError, match="unowned"):
        launch.prepare(root)
    assert events == [] and sorted(path.name for path in base.iterdir()) == ["canary"]


def test_cache_owned_by_another_checkout_is_refused(installation):
    root, base, events = installation
    launch.prepare(root)
    owner = base / "owner.json"
    record = json.loads(owner.read_bytes())
    record["source_root"] = str(root.parent / "other-checkout")
    owner.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ValueError, match="another purpose or checkout"):
        launch.prepare(root)
    assert len(events) == 1 and json.loads(owner.read_bytes()) == record


def test_failed_installation_publishes_no_active_pointer_and_retains_its_diagnostics(installation, monkeypatch):
    root, base, _ = installation

    def fail(home: Path):
        home.mkdir()
        (home / "partial.log").write_text("download failed", encoding="utf-8")
        raise OSError("Controlled installation failure")

    monkeypatch.setattr(launch.provider, "setup", fail)
    with pytest.raises(OSError, match="Controlled installation failure"):
        launch.prepare(root)
    assert not list(base.glob("active-*.json"))
    assert len(list(base.glob("profile-*/partial.log"))) == 1
    record = json.loads(next(base.glob("logs/*/setup-failure.json")).read_bytes())
    assert record["failure"] == "Controlled installation failure"


def test_changed_qualified_inputs_create_a_separate_profile(installation, monkeypatch):
    root, base, _ = installation
    first, _ = launch.prepare(root)
    monkeypatch.setattr(launch, "identity", lambda _, name="cocoindex": "b" * 64)
    second, result = launch.prepare(root)
    assert first != second and first.is_dir() and second.is_dir()
    assert len(list(base.glob("active-*.json"))) == 2
    assert result["automatic_setup"]["newly_installed"] is True


def test_crawler_recovery_is_separate_from_the_index_provider(installation, monkeypatch):
    root, index_cache, _ = installation
    monkeypatch.setattr(launch.crawler, "setup", launch.provider.setup)
    monkeypatch.setattr(launch.crawler, "verify", launch.provider.verify)
    index, _ = launch.prepare(root)
    first, result = launch.prepare(root, "crawl4ai")
    reused, reuse = launch.prepare(root, "crawl4ai")
    assert first == reused and first.parent.name == "automatic-crawl4ai"
    assert result["automatic_setup"]["newly_installed"] and not reuse["automatic_setup"]["newly_installed"]
    (first / "package.txt").unlink()
    recovered, recovery = launch.prepare(root, "crawl4ai")
    assert recovered != first and first.exists()
    assert recovery["automatic_setup"]["recovered_previous_profile"]
    assert index.parent == index_cache and (index / "package.txt").read_text() == "qualified"


def test_provider_children_do_not_modify_the_admitted_interpreter_bytecode(tmp_path):
    environment = launch.owned.profile_environment(tmp_path, {})
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"


def test_automatic_profiles_share_a_private_package_cache_without_changing_host_configuration(
    installation, monkeypatch
):
    root, base, _ = installation
    first, _ = launch.prepare(root)
    second = base / "profile-ffffffffffff"
    second.mkdir()
    directory = root / "toolchains/cocoindex-code"
    directory.mkdir(parents=True)
    (directory / "source.json").write_text(json.dumps({"source_date_epoch": 0}), encoding="utf-8")
    monkeypatch.setattr(launch.provider, "ROOT", root)
    monkeypatch.setenv("PIP_CACHE_DIR", str(root.parent / "unrelated"))
    left = launch.provider.environment(first)
    right = launch.provider.environment(second)
    assert left["PIP_CACHE_DIR"] == right["PIP_CACHE_DIR"] == str(base / "package-cache")
    assert Path(left["PIP_CACHE_DIR"]).is_dir() and not (root.parent / "unrelated").exists()
