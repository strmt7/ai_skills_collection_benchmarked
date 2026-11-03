"""Independent output-routing controls for trusted Click source variants."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

SOURCE = Path(os.environ["CLICK_CONTROL_SOURCE"]).resolve()
sys.path.insert(0, str(SOURCE))
import click  # noqa: E402
from click.testing import CliRunner  # noqa: E402

if not Path(click.__file__).resolve().is_relative_to(SOURCE):
    raise RuntimeError("Click was imported from outside the selected source")


def invoke(kind: str, *, err: bool) -> tuple[str, str]:
    @click.command()
    def command() -> None:
        value = getattr(click, kind)("Question", prompt_suffix=": ", show_default=False, err=err)
        click.echo(f"RESULT={value}")

    answer = "hello\n" if kind == "prompt" else "y\n"
    result = CliRunner().invoke(command, input=answer)
    if result.exception is not None:
        raise result.exception
    if result.exit_code != 0:
        raise RuntimeError("Prompt command failed")
    expected_result = "RESULT=hello\n" if kind == "prompt" else "RESULT=True\n"
    if not result.stdout.endswith(expected_result):
        raise AssertionError("Prompt result was not returned on stdout")
    return result.stdout, result.stderr


class Contract(unittest.TestCase):
    def test_prompt_to_stderr(self) -> None:
        stdout, stderr = invoke("prompt", err=True)
        self.assertIn("Question", stderr)
        self.assertNotIn("Question", stdout)

    def test_prompt_to_stdout(self) -> None:
        stdout, stderr = invoke("prompt", err=False)
        self.assertIn("Question", stdout)
        self.assertNotIn("Question", stderr)

    def test_confirm_to_stderr(self) -> None:
        stdout, stderr = invoke("confirm", err=True)
        self.assertIn("Question", stderr)
        self.assertNotIn("Question", stdout)

    def test_confirm_to_stdout(self) -> None:
        stdout, stderr = invoke("confirm", err=False)
        self.assertIn("Question", stdout)
        self.assertNotIn("Question", stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
