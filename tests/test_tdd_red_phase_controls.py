"""Exercise why an exit code alone does not establish a meaningful red phase."""

import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def test_pytest_exit_status_requires_case_level_interpretation(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "import pytest\n"
        "def test_behavior():\n    assert 1 + 1 == 3\n"
        "@pytest.fixture\ndef broken_setup():\n    raise RuntimeError('setup failure')\n"
        "def test_setup(broken_setup):\n    pass\n"
        "@pytest.mark.skip(reason='not executed')\ndef test_skipped():\n    assert False\n"
        "def test_passed():\n    assert 1 + 1 == 2\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    report = tmp_path / "report.xml"
    command = [sys.executable, "-m", "pytest", "-q", "-c", "pytest.ini", "test_sample.py"]
    result = subprocess.run(
        [*command, "--junitxml", str(report)], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 1, result.stdout + result.stderr
    cases = {case.attrib["name"]: case for case in ET.parse(report).iter("testcase")}
    assert set(cases) == {"test_behavior", "test_setup", "test_skipped", "test_passed"}
    assert cases["test_behavior"].find("failure") is not None
    assert cases["test_setup"].find("error") is not None
    assert cases["test_skipped"].find("skipped") is not None
    assert len(cases["test_passed"]) == 0

    for name, outcome in (("test_behavior", "failure"), ("test_setup", "error")):
        single_report = tmp_path / f"{name}.xml"
        single = subprocess.run(
            [*command[:-1], f"test_sample.py::{name}", "--junitxml", str(single_report)],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert single.returncode == 1, single.stdout + single.stderr
        observed = list(ET.parse(single_report).iter("testcase"))
        assert len(observed) == 1 and observed[0].attrib["name"] == name
        assert observed[0].find(outcome) is not None

    empty_report = tmp_path / "empty.xml"
    empty = subprocess.run(
        [*command, "-k", "no_matching_test", "--junitxml", str(empty_report)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert empty.returncode == 5, empty.stdout + empty.stderr
    assert list(ET.parse(empty_report).iter("testcase")) == []
