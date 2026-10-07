"""Trusted POSIX publication controls, invoked inside the bounded Docker backend."""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

sys.path[:0] = ["/submission/tools", "/submission/vendor"]


def run(request):
    import _catalog_publication as publication
    import build_catalog as catalog

    checks = []
    with tempfile.TemporaryDirectory(prefix="catalog-posix-", dir="/tmp") as temporary:
        root = Path(temporary) / "workspace"
        root.mkdir()
        (root / "data").mkdir()
        (root / "data/catalog.json").write_text("original metadata")
        original = root / "included/skills"
        original.mkdir(parents=True)
        (original / "SKILL.md").write_text("original skill")
        outputs = ("data/catalog.json", "included/skills")

        def build(stage):
            (stage / "data").mkdir()
            (stage / "data/catalog.json").write_text("replacement metadata")
            skill = stage / "included/skills"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("replacement skill")
            (skill / "script").write_text("#!/bin/sh\nexit 0\n")
            (skill / "script").chmod(0o755)

        transaction, journal = publication.prepare(root, outputs, build)
        publication.publish(root, transaction, journal)
        assert (root / "data/catalog.json").read_text() == "replacement metadata"
        assert (original / "SKILL.md").read_text() == "replacement skill"
        assert stat.S_IMODE((original / "script").stat().st_mode) == 0o755
        assert (transaction / "previous/data/catalog.json").read_text() == "original metadata"
        checks.append("publication_preserves_posix_executable_mode_and_previous_files")

        transaction, journal = publication.prepare(root, outputs, build)
        assert publication.differences(root, transaction, journal) == []
        checks.append("repeated_posix_stage_has_no_drift")

        rename = Path.rename

        def fail(path, target):
            if path == transaction / "generated/included/skills":
                raise OSError("controlled later replacement failure")
            return rename(path, target)

        Path.rename = fail
        try:
            try:
                publication.publish(root, transaction, journal)
                raise AssertionError("expected publication failure")
            except OSError as exc:
                assert "controlled later" in str(exc)
        finally:
            Path.rename = rename
        assert (root / "data/catalog.json").read_text() == "replacement metadata"
        assert (original / "SKILL.md").read_text() == "replacement skill"
        assert journal["status"] == "rolled_back"
        checks.append("later_posix_rename_failure_restores_earlier_outputs")

        link = root / "linked-output"
        link.symlink_to(root / "included", target_is_directory=True)
        try:
            publication.prepare(root, ("linked-output/skills",), lambda stage: None)
            raise AssertionError("symlink target was accepted")
        except ValueError as exc:
            assert "linked publication" in str(exc)
        link.unlink()
        checks.append("posix_symlink_publication_target_rejected")

        source, copied = root / "source", root / "copied"
        source.mkdir()
        (source / "SKILL.md").write_text("# Executable resource\n")
        executable = source / "no-extension"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        modes = {"SKILL.md": "100644", "no-extension": "100755"}
        expected = catalog.sha256_tree(source, file_modes=modes)
        catalog.copy_sanitized_tree(source, copied, file_modes=modes)
        assert catalog.sha256_tree(copied, file_modes=modes) == expected
        assert stat.S_IMODE((copied / "no-extension").stat().st_mode) == 0o755
        executable.chmod(0o644)
        try:
            catalog.sha256_tree(source, file_modes=modes)
            raise AssertionError("changed executable mode was accepted")
        except ValueError as exc:
            assert "executable mode differs" in str(exc)
        checks.append("portable_tree_hash_copy_and_posix_mode_tamper_detection")
    return {
        "platform": sys.platform,
        "uid": os.getuid(),
        "checks": checks,
        "fixture_temporary_directory_removed": not Path(temporary).exists(),
        "scope": "POSIX filesystem contracts only; not the complete Linux suite or agent efficacy",
    }
