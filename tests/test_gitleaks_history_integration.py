"""Exercise the real Gitleaks gate against isolated Git histories."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GITLEAKS = os.environ.get("GITLEAKS_TEST_BINARY", "")
GIT = os.environ.get("GITLEAKS_TEST_GIT", "")
EXPECTED = os.environ.get("GITLEAKS_TEST_SHA256", "")


@unittest.skipUnless(GITLEAKS and GIT and EXPECTED, "verified Gitleaks and Git are not configured")
class HistoryGateIntegration(unittest.TestCase):
    """Test real scanner behavior without modifying the project checkout."""

    def setUp(self):
        """Create a private fixture repository with a non-sensitive base file."""
        self.temp = tempfile.TemporaryDirectory(prefix="gitleaks-integration-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.hooks = self.root / "empty-hooks"
        self.hooks.mkdir()
        self.template = self.root / "empty-template"
        self.template.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
        self.env.update(
            GIT_AUTHOR_NAME="Fixture",
            GIT_AUTHOR_EMAIL="fixture@example.invalid",
            GIT_COMMITTER_NAME="Fixture",
            GIT_COMMITTER_EMAIL="fixture@example.invalid",
        )
        self.git("init", "-b", "main", "--quiet")
        (self.repo / "plain.txt").write_text("fixture\n", encoding="utf-8")
        self.git("add", "plain.txt")
        self.git("commit", "--quiet", "-m", "Base")
        (self.repo / ".gitleaks.toml").write_bytes((ROOT / ".gitleaks.toml").read_bytes())

    def git(self, *args):
        """Use the explicitly supplied Git executable in the isolated fixture."""
        return subprocess.run(
            [
                GIT,
                "-c",
                "core.longpaths=true",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=" + str(self.hooks),
                "-c",
                "init.templateDir=" + str(self.template),
                "-C",
                str(self.repo),
                *args,
            ],
            env=self.env,
            capture_output=True,
            check=True,
        )

    def scan(self, *, git=None, scanner=None, expected=None):
        """Run the real gate and decode its machine-readable result."""
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                str(ROOT / "tools/check_gitleaks_history.py"),
                "--gitleaks",
                scanner or GITLEAKS,
                "--gitleaks-sha256",
                expected or EXPECTED,
                "--git",
                git or GIT,
                "--repository",
                str(self.repo),
                "--json",
            ],
            env=self.env,
            capture_output=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(result.stderr, b"")
        return result.returncode, json.loads(result.stdout)

    def add_finding(self, filename, *, inline_allow=False):
        """Write a deterministic non-secret digest in a generic assignment."""
        value = hashlib.sha256(b"public integration fixture").hexdigest()
        comment = " # gitleaks" + ":allow" if inline_allow else ""
        (self.repo / filename).write_text("api" + '_key = "' + value + '"' + comment + "\n", encoding="utf-8")
        self.git("add", filename)
        return value

    def test_clean_history_passes(self):
        """A complete scan of a harmless history succeeds."""
        code, result = self.scan()
        self.assertEqual(code, 0)
        self.assertTrue(result["passed"])

    def test_merge_only_finding_is_detected_and_redacted(self):
        """Inspect each merge parent rather than skipping merge-only content."""
        self.git("checkout", "-b", "side", "--quiet")
        (self.repo / "side.txt").write_text("side\n", encoding="utf-8")
        self.git("add", "side.txt")
        self.git("commit", "--quiet", "-m", "Side")
        self.git("checkout", "main", "--quiet")
        (self.repo / "main.txt").write_text("main\n", encoding="utf-8")
        self.git("add", "main.txt")
        self.git("commit", "--quiet", "-m", "Main")
        self.git("merge", "--no-commit", "--no-ff", "side")
        value = self.add_finding("merge-only.txt")
        self.git("commit", "--quiet", "-m", "Merge fixture")
        code, result = self.scan()
        self.assertEqual(code, 1)
        self.assertFalse(result["passed"])
        self.assertNotIn(value, result["redacted_output"])
        self.assertIn("REDACTED", result["redacted_output"])

    def test_inline_allow_comment_cannot_hide_a_finding(self):
        """Ignore source comments that would suppress an otherwise valid finding."""
        value = self.add_finding("allowed.txt", inline_allow=True)
        self.git("commit", "--quiet", "-m", "Inline fixture")
        code, result = self.scan()
        self.assertEqual(code, 1)
        self.assertFalse(result["passed"])
        self.assertNotIn(value, result["redacted_output"])

    def test_repository_ignore_file_cannot_hide_a_finding(self):
        """Ignore repository-supplied fingerprints when enforcing the gate."""
        value = self.add_finding("ignored.txt")
        self.git("commit", "--quiet", "-m", "Ignore fixture")
        first_code, first = self.scan()
        self.assertEqual(first_code, 1)
        match = re.search(r"(?m)^Fingerprint:\s*(.+)$", first["redacted_output"])
        self.assertIsNotNone(match)
        if match is None:
            raise AssertionError("Scanner did not emit the finding fingerprint")
        (self.repo / ".gitleaksignore").write_text(match.group(1) + "\n", encoding="utf-8")
        second_code, second = self.scan()
        self.assertEqual(second_code, 2)
        self.assertFalse(second["passed"])
        self.assertEqual(second["reason"], "scanner_diagnostics")
        self.assertEqual(second["error"], "Repository contains a Gitleaks ignore file")
        self.assertNotIn(value, second["redacted_output"])

    @unittest.skipIf(sys.platform == "win32", "the fault fixture uses a POSIX executable script")
    def test_git_diagnostic_with_zero_exit_is_rejected(self):
        """Fail when Git reports an error even if Gitleaks exits zero."""
        fake_dir = self.root / "fake"
        fake_dir.mkdir()
        fake = fake_dir / "git"
        marker = self.root / "git-log-marker"
        self.env["GATE_FIXTURE_LOG_MARKER"] = str(marker)
        fake.write_text(
            "#!" + sys.executable + "\n"
            "import os, sys\n"
            "if 'log' in sys.argv[1:]:\n"
            " open(os.environ['GATE_FIXTURE_LOG_MARKER'], 'w').write('called')\n"
            " os.write(2, b'fixture git diagnostic\\n'); sys.exit(0)\n"
            "os.execv(" + repr(GIT) + ", ['git', *sys.argv[1:]])\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        code, result = self.scan(git=str(fake))
        self.assertEqual(code, 2)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "scanner_diagnostics")
        self.assertTrue(marker.is_file())

    @unittest.skipIf(sys.platform == "win32", "the path-hijack fixture uses a POSIX executable script")
    def test_repository_git_cannot_hijack_the_scan(self):
        """A repository-local fake Git executable must never be invoked."""
        marker = self.root / "repo-git-marker"
        self.env["GATE_FIXTURE_HIJACK_MARKER"] = str(marker)
        fake = self.repo / "git"
        fake.write_text(
            "#!" + sys.executable + "\n"
            "import os, sys\n"
            "open(os.environ['GATE_FIXTURE_HIJACK_MARKER'], 'w').write('called')\n"
            "sys.exit(1)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        code, result = self.scan()
        self.assertEqual(code, 0)
        self.assertTrue(result["passed"])
        self.assertFalse(marker.exists())

    def test_detached_head_finding_is_detected(self):
        """Scan detached HEAD even when no branch points at its commit."""
        self.git("checkout", "--detach", "--quiet")
        value = self.add_finding("detached.txt")
        self.git("commit", "--quiet", "-m", "Detached fixture")
        code, result = self.scan()
        self.assertEqual(code, 1)
        self.assertFalse(result["passed"])
        self.assertNotIn(value, result["redacted_output"])

    @unittest.skipIf(sys.platform == "win32", "the drift fixture uses a POSIX executable script")
    def test_ref_change_during_scan_is_rejected(self):
        """Fail when the scanner observes a changing repository reference set."""
        fake = self.root / "fake-scanner"
        fake.write_text(
            "#!" + sys.executable + "\n"
            "import subprocess, sys\n"
            "subprocess.run([" + repr(GIT) + ", '-C', sys.argv[-1], 'update-ref', "
            "'refs/heads/fixture-drift', 'HEAD'], check=True)\n",
            encoding="utf-8",
        )
        fake.chmod(0o755)
        expected = hashlib.sha256(fake.read_bytes()).hexdigest()
        code, result = self.scan(scanner=str(fake), expected=expected)
        self.assertEqual(code, 2)
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "scanner_diagnostics")
        self.git("rev-parse", "--verify", "refs/heads/fixture-drift")


if __name__ == "__main__":
    if not (GITLEAKS and GIT and EXPECTED):
        raise SystemExit("Verified Gitleaks, Git and binary SHA-256 are required")
    unittest.main()
