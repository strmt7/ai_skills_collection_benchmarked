"""Independent subprocess controls for skipped unittest lifecycles under pytest."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(os.environ["PYTEST_TARGET_SOURCE"]).resolve()
TARGET_PYTHON = Path(os.environ["PYTEST_TARGET_PYTHON"]).absolute()


def exercise(decorator, scope, pdb, expected_events, expected_skipped):
    with tempfile.TemporaryDirectory(prefix="pytest-skip-contract-") as directory:
        root = Path(directory)
        log = root / "events.txt"
        mark_class = decorator if scope in ("class", "inherited") else ""
        mark_method = f"    {decorator}\n" if scope == "method" else ""
        parent = "Base" if scope == "inherited" else "unittest.TestCase"
        parent_class = f"{mark_class}\nclass Base(unittest.TestCase):\n    pass\n\n" if scope == "inherited" else ""
        class_mark = "" if scope == "inherited" else mark_class
        source = f"""import sys
import unittest
import pytest
from pathlib import Path
import _pytest.unittest as pytest_unittest
assert sys.prefix != sys.base_prefix
assert Path(pytest_unittest.__file__).resolve() == Path({str(SOURCE / "src/_pytest/unittest.py")!r}).resolve()
LOG = Path({str(log)!r})
def record(value):
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(value + "\\n")
{parent_class}
{class_mark}
class TestExample({parent}):
    @classmethod
    def setUpClass(cls): record("class_setup")
    @classmethod
    def tearDownClass(cls): record("class_teardown")
    def setUp(self): record("setup")
    def tearDown(self): record("teardown")
{mark_method}    def test_example(self): record("test")
"""
        (root / "test_example.py").write_text(source, encoding="utf-8")
        (root / "pytest.ini").write_text("[pytest]\naddopts =\n", encoding="utf-8")
        env = dict(
            os.environ, PYTHONPATH=str(SOURCE / "src"), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1"
        )
        env.pop("PYTEST_ADDOPTS", None)
        env.pop("PYTEST_PLUGINS", None)
        command = [str(TARGET_PYTHON), "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_example.py"]
        if pdb:
            command.append("--pdb")
        proc = subprocess.run(
            command, cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=25
        )
        events = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        if proc.returncode != 0:
            raise AssertionError(f"pytest returned {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        if events != expected_events:
            raise AssertionError(f"Expected {expected_events}, got {events}\n{proc.stdout}\n{proc.stderr}")
        marker = "1 skipped" if expected_skipped else "1 passed"
        if marker not in proc.stdout:
            raise AssertionError(f"Missing {marker!r}\n{proc.stdout}\n{proc.stderr}")


class Contract(unittest.TestCase):
    def test_failed_test_enters_debugger_before_teardown(self):
        with tempfile.TemporaryDirectory(prefix="pytest-debug-order-") as directory:
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
            (root / "test_example.py").write_text(
                f"""import sys
import unittest
from pathlib import Path
import _pytest.unittest as pytest_unittest
assert sys.prefix != sys.base_prefix
assert Path(pytest_unittest.__file__).resolve() == Path({str(SOURCE / "src/_pytest/unittest.py")!r}).resolve()
def record(value):
    with Path({str(log)!r}).open("a", encoding="utf-8") as stream: stream.write(value + "\\n")
class TestExample(unittest.TestCase):
    def setUp(self): record("setup")
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
            command = [
                str(TARGET_PYTHON),
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--pdb",
                "--pdbcls=debug_probe:Probe",
                "test_example.py",
            ]
            proc = subprocess.run(
                command, cwd=root, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=25
            )
            events = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertIn("1 failed", proc.stdout)
            self.assertEqual(events, ["setup", "test", "debugger", "teardown"], proc.stdout + proc.stderr)


def make_test(decorator, scope, pdb, expected_events, expected_skipped):
    def test(self):
        exercise(decorator, scope, pdb, expected_events, expected_skipped)

    return test


for mode, pdb in (("normal", False), ("pdb", True)):
    for name, decorator in (
        ("skip", '@unittest.skip("reason")'),
        ("skipif", '@unittest.skipIf(True, "reason")'),
        ("skipunless", '@unittest.skipUnless(False, "reason")'),
    ):
        for scope in ("class", "method", "inherited"):
            expected = ["class_setup", "class_teardown"] if scope == "method" else []
            setattr(Contract, f"test_{scope}_{name}_{mode}", make_test(decorator, scope, pdb, expected, True))
    for scope in ("class", "method"):
        setattr(
            Contract,
            f"test_{scope}_pytest_skip_{mode}",
            make_test('@pytest.mark.skip(reason="reason")', scope, pdb, [], True),
        )
    expected = ["class_setup", "setup", "test", "teardown", "class_teardown"]
    setattr(
        Contract,
        f"test_non_skipped_class_{mode}",
        make_test('@unittest.skipIf(False, "reason")', "class", pdb, expected, False),
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
