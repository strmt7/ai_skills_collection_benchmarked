"""Exercise the installed overlay's public generator interface on the current host."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_cpp_overlay_file_and_available_build_controls() -> None:
    package = Path(__file__).resolve().parents[1] / "included/improved/skills/makefile-generator-cpp"
    result = subprocess.run(
        [sys.executable, "-B", "-m", "unittest", "discover", "-s", str(package), "-p", "test_generator.py", "-v"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
