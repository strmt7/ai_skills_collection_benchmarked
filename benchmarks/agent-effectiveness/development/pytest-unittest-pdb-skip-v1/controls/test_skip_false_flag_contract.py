"""Trusted controls for false class skip flags and debugger/teardown order."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(os.environ["PYTEST_TARGET_SOURCE"]).resolve()
TARGET_PYTHON = Path(os.environ["PYTEST_TARGET_PYTHON"]).absolute()


class Contract(unittest.TestCase):
    def exercise(self, inherited: bool) -> None:
        with tempfile.TemporaryDirectory(prefix="pytest-false-skip-") as directory:
            root = Path(directory)
            log = root / "events.txt"
            (root / "pytest.ini").write_text("[pytest]\naddopts =\n", encoding="utf-8")
            (root / "debug_probe.py").write_text(
                f"""import pdb
from pathlib import Path
class Probe(pdb.Pdb):
    def interaction(self, *args, **kwargs):
        with Path({str(log)!r}).open("a", encoding="utf-8") as stream: stream.write("debugger\\n")
""",
                encoding="utf-8",
            )
            parent = "Base" if inherited else "unittest.TestCase"
            base = "class Base(unittest.TestCase):\n    __unittest_skip__ = False\n" if inherited else ""
            flag = "" if inherited else "    __unittest_skip__ = False\n"
            (root / "test_example.py").write_text(
                f"""import sys
import unittest
from pathlib import Path
import _pytest.unittest as pytest_unittest
assert sys.prefix != sys.base_prefix
assert Path(pytest_unittest.__file__).resolve() == Path({str(SOURCE / "src/_pytest/unittest.py")!r}).resolve()
def record(value):
    with Path({str(log)!r}).open("a", encoding="utf-8") as stream: stream.write(value + "\\n")
{base}
class TestExample({parent}):
{flag}    def setUp(self): record("setup")
    def tearDown(self): record("teardown")
    def test_failure(self):
        record("test")
        self.fail("intentional control failure")
""",
                encoding="utf-8",
            )
            env = dict(
                os.environ,
                PYTHONPATH=os.pathsep.join([str(SOURCE / "src"), str(root)]),
                PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                PYTHONDONTWRITEBYTECODE="1",
            )
            env.pop("PYTEST_ADDOPTS", None)
            env.pop("PYTEST_PLUGINS", None)
            proc = subprocess.run(
                [
                    str(TARGET_PYTHON),
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--pdb",
                    "--pdbcls=debug_probe:Probe",
                    "test_example.py",
                ],
                cwd=root,
                env=env,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=25,
            )
            events = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("1 failed", proc.stdout)
            self.assertEqual(events, ["setup", "test", "debugger", "teardown"], proc.stdout + proc.stderr)

    def test_direct_false_flag_preserves_debugger_order(self) -> None:
        self.exercise(False)

    def test_inherited_false_flag_preserves_debugger_order(self) -> None:
        self.exercise(True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
