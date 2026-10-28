from __future__ import annotations

import hashlib
import io
import json
import stat
import zipfile
from pathlib import Path

import appcontainer_dependencies as dependencies
import appcontainer_runtime as runtime
import pytest


def package_fixture(tmp_path: Path, members: list[tuple[str, bytes, int]]) -> tuple[Path, dict]:
    archives = tmp_path / "archives"
    archives.mkdir()
    archive = archives / "fixture.whl"
    with zipfile.ZipFile(archive, "w") as wheel:
        for name, content, mode in members:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.external_attr = mode << 16
            wheel.writestr(info, content)
    data = archive.read_bytes()
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_STORED) as container:
        info = zipfile.ZipInfo(archive.name, (1980, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        info.compress_type = zipfile.ZIP_STORED
        container.writestr(info, data)
    bundled = bundle.getvalue()
    specification = {
        "archive_sha256": hashlib.sha256(bundled).hexdigest(),
        "archive_bytes": len(bundled),
        "packages": [
            {
                "name": "fixture",
                "filename": archive.name,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ],
        "files": {name: hashlib.sha256(content).hexdigest() for name, content, _ in members},
    }
    return archives, specification


def test_offline_dependency_graph_is_reproducible_and_complete(tmp_path, monkeypatch):
    archives, spec = package_fixture(tmp_path, [("sample/__init__.py", b"value = 1\n", stat.S_IFREG | 0o644)])
    monkeypatch.setattr(runtime, "_prepare_private_home", lambda home, specification: None)
    homes = [tmp_path / "first", tmp_path / "second"]
    for home in homes:
        dependencies.install_archives(home, spec, archives)
        assert runtime.verify(home, spec) == []
        assert json.loads((home / "source.json").read_text(encoding="utf-8")) == spec
    assert (homes[0] / "dependencies.zip").read_bytes() == (homes[1] / "dependencies.zip").read_bytes()
    with pytest.raises(FileExistsError):
        dependencies.install_archives(homes[0], spec, archives)


@pytest.mark.parametrize(
    "members,reason",
    [
        ([("../outside.py", b"x", stat.S_IFREG | 0o644)], "unsafe path"),
        ([("sample/link", b"target", stat.S_IFLNK | 0o777)], "wheel member"),
        ([("sample/hook.pth", b"x", stat.S_IFREG | 0o644)], "wheel member"),
        ([("sample/A.py", b"x", stat.S_IFREG | 0o644), ("sample/a.py", b"y", stat.S_IFREG | 0o644)], "duplicate paths"),
    ],
)
def test_unsafe_archive_members_fail_without_escaping(tmp_path, members, reason):
    archives, spec = package_fixture(tmp_path, members)
    home = tmp_path / "home"
    with pytest.raises(ValueError, match=reason):
        dependencies.install_archives(home, spec, archives)
    assert not (tmp_path / "outside.py").exists()
    assert not (home / "source.json").exists()


def test_changed_archive_is_rejected_before_extraction(tmp_path):
    archives, spec = package_fixture(tmp_path, [("sample/__init__.py", b"valid", stat.S_IFREG | 0o644)])
    (archives / "fixture.whl").write_bytes(b"changed")
    home = tmp_path / "home"
    with pytest.raises(ValueError, match="pinned bytes"):
        dependencies.install_archives(home, spec, archives)
    assert not (home / "runtime").exists()


@pytest.mark.parametrize(
    "url",
    [
        "http://files.pythonhosted.org/packages/a.whl",
        "https://files.pythonhosted.org.evil.example/packages/a.whl",
        "https://user@files.pythonhosted.org/packages/a.whl",
        "https://files.pythonhosted.org/packages/a.whl?token=ignored",
        "https://files.pythonhosted.org:8443/packages/a.whl",
    ],
)
def test_dependency_download_cannot_follow_untrusted_urls(url):
    assert not dependencies._official_package_url(url)
    with pytest.raises(ValueError, match="redirect"):
        dependencies._OfficialRedirect().redirect_request(None, None, 302, "", {}, url)


def test_expected_official_package_url_is_admitted():
    assert dependencies._official_package_url("https://files.pythonhosted.org/packages/example/package.whl")


def test_advisory_coordinates_match_the_pinned_dependency_archives():
    specification = json.loads(dependencies.SOURCE.read_text(encoding="utf-8"))
    requirements = (dependencies.SOURCE.parent / "requirements.txt").read_text(encoding="utf-8")
    lines = {line.strip() for line in requirements.splitlines() if line.strip() and not line.startswith("#")}
    expected = {
        f"{item['name'].lower()}=={item['version']} --hash=sha256:{item['sha256']}"
        for item in specification["packages"]
    }
    assert lines == expected


@pytest.mark.parametrize(
    "records",
    [
        [],
        [{"path": "a", "sha256": "f" * 64}, {"path": "a", "sha256": "e" * 64}],
        [{"path": "a", "sha256": "not a digest"}],
        [{"path": "a", "sha256": "f" * 64, "extra": True}],
    ],
)
def test_dependency_file_records_must_be_unambiguous(tmp_path, records):
    source = tmp_path / "source.json"
    source.write_text(json.dumps({"files": records}), encoding="utf-8")
    with pytest.raises(ValueError, match="inventory|record"):
        dependencies.load_specification(source)
