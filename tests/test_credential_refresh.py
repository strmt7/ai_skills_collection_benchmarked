"""Credential migration requires original public-source equivalence and retains recovery."""

from __future__ import annotations

import json
import subprocess

import _catalog_publication as publication
import build_catalog as catalog
import pytest
import refresh_credential_policy as refresh


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    sources = tmp_path / "sources"
    checkout = sources / "public-source"
    checkout.mkdir(parents=True)
    git(checkout, "init", "-q")
    git(checkout, "remote", "add", "origin", "https://github.com/example/public-source.git")
    for name in ("affected", "unaffected"):
        folder = checkout / name
        folder.mkdir()
        text = f"---\nname: {name}\ndescription: Demonstrate the contract.\n---\n# Example\n"
        if name == "affected":
            text += "server_key = '" + "sk_" + "test_" + "fixture" * 6 + "'\n"
        else:
            text += "Use the neutral documented contract.\n"
        (folder / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
    git(checkout, "add", ".")
    git(checkout, "-c", "user.name=AI agent", "-c", "user.email=", "commit", "-qm", "Owned source fixture")
    entries = []
    for name in ("affected", "unaffected"):
        source = checkout / name
        mirror = root / "included/skills" / name
        modes = catalog.skill_file_modes(source)
        catalog.copy_sanitized_tree(source, mirror, file_modes=modes)
        entries.append(
            {
                "id": name,
                "name": name,
                "description": "Demonstrate the contract.",
                "source_repo": "example/public-source",
                "source_path": name + "/SKILL.md",
                "mirrored_path": "included/skills/" + name,
                "commit_sha": git(checkout, "rev-parse", "HEAD"),
                "immutable_source_url": "https://github.com/example/public-source/blob/"
                + git(checkout, "rev-parse", "HEAD")
                + "/"
                + name
                + "/SKILL.md",
                "skill_file_sha256": catalog.sha256_file(source / "SKILL.md"),
                "skill_dir_sha256": catalog.sha256_tree(source, file_modes=modes),
                "file_modes": modes,
            }
        )
    source = {
        "repo": "example/public-source",
        "local_dir": "public-source",
        "commit_sha": git(checkout, "rev-parse", "HEAD"),
        "tree_sha": git(checkout, "rev-parse", "HEAD^{tree}"),
        "skills": [dict(entry) for entry in entries],
    }
    values = [entries, {"sources": [source]}, entries, [entries[0]]]
    for relative, value in zip(refresh.METADATA, values, strict=True):
        catalog.write_json(root / relative, value)
    monkeypatch.setattr(refresh, "ROOT", root)
    return root, sources, checkout


def test_refresh_stages_then_publishes_only_changed_locked_sources(fixture):
    root, sources, checkout = fixture
    originals = {p: publication.signature(root / p) for p in refresh.METADATA}
    unrelated = publication.signature(root / "included/skills/unaffected")
    upstream = publication.signature(checkout)
    transaction, journal, count = refresh.prepare_refresh(root, sources, "artifacts/refresh.json")
    assert count == 1
    assert all(publication.signature(root / p) == value for p, value in originals.items())
    staged = transaction / "generated"
    receipt = json.loads((staged / "artifacts/refresh.json").read_text())
    assert receipt["sources_upgraded"] is False
    assert receipt["findings_suppressed"] is False
    assert len(receipt["updates"][0]["changed_resources"]) == 1
    assert receipt["updates"][0]["previous"]["credential_policy_version"] is None
    assert receipt["updates"][0]["updated"]["credential_policy_version"] == 2
    publication.publish(root, transaction, journal)
    assert "<STRIPE_SERVER_KEY>" in (root / "included/skills/affected/SKILL.md").read_text()
    assert publication.signature(root / "included/skills/unaffected") == unrelated
    assert publication.signature(checkout) == upstream
    for relative in refresh.METADATA:
        records = refresh.read(root / relative)
        if relative == "data/source_lock.json":
            records = records["sources"][0]["skills"]
        affected = next(record for record in records if record["id"] == "affected")
        assert affected["credential_policy_version"] == 2
        assert affected["skill_dir_sha256"] == catalog.sha256_tree(
            root / "included/skills/affected", file_modes=affected["file_modes"]
        )
        assert publication.signature(transaction / "previous" / relative) == originals[relative]
    assert (
        refresh.main(["--source-root", str(sources), "--receipt", "artifacts/refresh.json", "--check", "--json"]) == 0
    )


@pytest.mark.parametrize("tamper", ["mirror", "source", "head", "origin", "lock"])
def test_unverified_input_fails_before_publication(fixture, tamper):
    root, sources, checkout = fixture
    if tamper == "mirror":
        (root / "included/skills/affected/SKILL.md").write_text("different mirror")
    elif tamper == "source":
        (checkout / "affected/SKILL.md").write_text("dirty original")
    elif tamper == "head":
        git(
            checkout,
            "-c",
            "user.name=AI agent",
            "-c",
            "user.email=",
            "commit",
            "--allow-empty",
            "-qm",
            "Owned different head",
        )
    elif tamper == "origin":
        git(checkout, "remote", "set-url", "origin", "https://github.com/example/wrong")
    else:
        data = refresh.read(root / "data/source_lock.json")
        data["sources"][0]["skills"][0]["skill_dir_sha256"] = "0" * 64
        catalog.write_json(root / "data/source_lock.json", data)
    before = publication.signature(root)
    with pytest.raises(ValueError):
        refresh.prepare_refresh(root, sources, "artifacts/refresh.json")
    assert publication.signature(root) == before


def test_check_mode_records_no_publication(fixture, capsys):
    root, sources, _ = fixture
    before = {p: publication.signature(root / p) for p in refresh.METADATA}
    assert (
        refresh.main(["--source-root", str(sources), "--receipt", "artifacts/refresh.json", "--check", "--json"]) == 1
    )
    result = json.loads(capsys.readouterr().out)
    assert result["updates"] == 1
    assert result["mode"] == "check"
    assert not (root / "artifacts/refresh.json").exists()
    assert all(publication.signature(root / p) == value for p, value in before.items())


def test_existing_receipt_is_never_overwritten(fixture):
    root, sources, _ = fixture
    (root / "artifacts").mkdir()
    (root / "artifacts/receipt.json").write_text("keep original")
    with pytest.raises(ValueError, match="new file"):
        refresh.prepare_refresh(root, sources, "artifacts/receipt.json")
    assert (root / "artifacts/receipt.json").read_text() == "keep original"


def test_cli_reports_missing_source_as_failure(fixture, capsys):
    _, sources, _ = fixture
    assert (
        refresh.main(["--source-root", str(sources / "missing"), "--receipt", "artifacts/receipt.json", "--json"]) == 2
    )
    assert json.loads(capsys.readouterr().out)["ok"] is False


@pytest.mark.parametrize("path", ["README.json", "artifacts/../outside.json", "artifacts/wrong.txt"])
def test_receipt_scope_is_checked_before_generation(fixture, path):
    root, sources, _ = fixture
    with pytest.raises(ValueError):
        refresh.prepare_refresh(root, sources, path)
    assert not (root / ".venv/generation-staging").exists()


def test_changed_public_input_cannot_reuse_old_canonical_hashes(fixture):
    root, sources, checkout = fixture
    (checkout / "affected/SKILL.md").write_text("different committed original", encoding="utf-8")
    git(checkout, "add", ".")
    git(checkout, "-c", "user.name=AI agent", "-c", "user.email=", "commit", "-qm", "Owned changed source")
    entries = refresh.read(root / "data/skills_catalog.json")
    lock = refresh.read(root / "data/source_lock.json")
    lock["sources"][0]["commit_sha"] = git(checkout, "rev-parse", "HEAD")
    lock["sources"][0]["tree_sha"] = git(checkout, "rev-parse", "HEAD^{tree}")
    for entry in entries:
        entry["commit_sha"] = lock["sources"][0]["commit_sha"]
    catalog.write_json(root / "data/skills_catalog.json", entries)
    catalog.write_json(root / "data/source_lock.json", lock)
    with pytest.raises(ValueError, match="does not reproduce"):
        refresh.prepare_refresh(root, sources, "artifacts/refresh.json")


@pytest.mark.parametrize("ascii_only", [True, False])
def test_metadata_preserves_field_order_and_unicode_escaping(ascii_only):
    old = {"z": "café", "a": True}
    raw = (json.dumps(old, ensure_ascii=ascii_only, indent=2) + "\n").replace("\n", "\r\n").encode()
    updated = old | {"policy": 2}
    assert (
        refresh.metadata_bytes(updated, raw) == (json.dumps(updated, ensure_ascii=ascii_only, indent=2) + "\n").encode()
    )


def test_unknown_metadata_format_is_rejected():
    with pytest.raises(ValueError, match="two-space"):
        refresh.metadata_bytes({}, b'{"a": 1}')
