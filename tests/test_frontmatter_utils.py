import json
import subprocess
import sys
from pathlib import Path

from _lib_b.frontmatter_utils import parse


def test_read_relocated_windows_skill_bytes_without_changing_markdown():
    body = "# Verify changes\r\n\r\nKeep the original body.\r\n"
    text = "---\r\nname: verification\r\ndescription: Verify changes.\r\n---\r\n" + body

    assert parse(text) == ({"name": "verification", "description": "Verify changes."}, body)


def test_prefix_of_body_line_cannot_end_frontmatter():
    text = "---\nname: verification\n---not-a-delimiter\n"

    assert parse(text) == ({}, text)


def test_native_trial_does_not_load_or_bind_the_skill_frontmatter_parser():
    tools = Path(__file__).resolve().parents[1] / "tools"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-c",
            "import json, sys; sys.path.insert(0, sys.argv[1]); "
            "from qualify_trial_context import SOURCES; "
            "from _native_trial_plan import execution_sources; "
            "print(json.dumps({'loaded': '_lib_b.frontmatter_utils' in sys.modules, "
            "'trial_bound': 'tools/_lib_b/frontmatter_utils.py' in execution_sources(), "
            "'context_bound': 'tools/_lib_b/frontmatter_utils.py' in SOURCES, "
            "'signin_bound': 'tools/_trial_signin.py' in SOURCES}))",
            str(tools),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )

    assert json.loads(result.stdout) == {
        "loaded": False,
        "trial_bound": False,
        "context_bound": False,
        "signin_bound": True,
    }
