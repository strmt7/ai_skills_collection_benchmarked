"""Behavior controls for trusted Click source variants, independent of skill text."""

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


def invoke(kind: str, suffix: str, answer: str, **options: object) -> tuple[int, str]:
    @click.command()
    def command() -> None:
        value = getattr(click, kind)("Question", prompt_suffix=suffix, **options)
        click.echo(f"RESULT={value}")

    result = CliRunner().invoke(command, input=answer)
    if result.exception is not None:
        raise result.exception
    return result.exit_code, result.output


class Contract(unittest.TestCase):
    def test_prompt_empty_suffix(self) -> None:
        self.assertEqual(invoke("prompt", "", "hello\n", show_default=False), (0, "Questionhello\nRESULT=hello\n"))

    def test_prompt_punctuation_suffix(self) -> None:
        self.assertEqual(invoke("prompt", ":", "hello\n", show_default=False), (0, "Question:hello\nRESULT=hello\n"))

    def test_prompt_default_suffix(self) -> None:
        self.assertEqual(invoke("prompt", ": ", "hello\n", show_default=False), (0, "Question: hello\nRESULT=hello\n"))

    def test_prompt_single_space_suffix(self) -> None:
        self.assertEqual(invoke("prompt", " ", "hello\n", show_default=False), (0, "Question hello\nRESULT=hello\n"))

    def test_prompt_double_space_suffix(self) -> None:
        self.assertEqual(invoke("prompt", "  ", "hello\n", show_default=False), (0, "Question  hello\nRESULT=hello\n"))

    def test_prompt_unicode_suffix(self) -> None:
        self.assertEqual(invoke("prompt", "λ", "hello\n", show_default=False), (0, "Questionλhello\nRESULT=hello\n"))

    def test_confirm_empty_suffix(self) -> None:
        self.assertEqual(invoke("confirm", "", "yes\n", show_default=False), (0, "Questionyes\nRESULT=True\n"))

    def test_confirm_punctuation_suffix(self) -> None:
        self.assertEqual(invoke("confirm", ":", "yes\n", show_default=False), (0, "Question:yes\nRESULT=True\n"))

    def test_confirm_default_suffix(self) -> None:
        self.assertEqual(invoke("confirm", ": ", "yes\n", show_default=False), (0, "Question: yes\nRESULT=True\n"))

    def test_confirm_single_space_suffix(self) -> None:
        self.assertEqual(invoke("confirm", " ", "yes\n", show_default=False), (0, "Question yes\nRESULT=True\n"))

    def test_confirm_double_space_suffix(self) -> None:
        self.assertEqual(invoke("confirm", "  ", "yes\n", show_default=False), (0, "Question  yes\nRESULT=True\n"))

    def test_confirm_unicode_suffix(self) -> None:
        self.assertEqual(invoke("confirm", "λ", "yes\n", show_default=False), (0, "Questionλyes\nRESULT=True\n"))

    def test_prompt_default_value(self) -> None:
        self.assertEqual(invoke("prompt", "", "\n", default="fallback"), (0, "Question [fallback]\nRESULT=fallback\n"))

    def test_confirm_default_value(self) -> None:
        self.assertEqual(invoke("confirm", "", "\n", default=False), (0, "Question [y/N]\nRESULT=False\n"))

    def test_prompt_retry(self) -> None:
        self.assertEqual(
            invoke("prompt", "", "bad\n42\n", type=int, show_default=False),
            (0, "Questionbad\nError: 'bad' is not a valid integer.\nQuestion42\nRESULT=42\n"),
        )

    def test_confirm_retry(self) -> None:
        self.assertEqual(
            invoke("confirm", "", "maybe\nyes\n", show_default=False),
            (0, "Questionmaybe\nError: invalid input\nQuestionyes\nRESULT=True\n"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
