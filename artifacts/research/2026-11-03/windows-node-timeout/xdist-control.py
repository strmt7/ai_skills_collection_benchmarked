import importlib.util
import os
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("e2e_control_original", os.environ["E2E_CONTROL_TEST"])
assert spec and spec.loader
original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original)


@pytest.mark.parametrize("iteration", range(120))
def test_original_control(tmp_path: Path, iteration: int) -> None:
    original.test_control_rejects_unreviewed_overlay_before_loading_dependencies(tmp_path)
