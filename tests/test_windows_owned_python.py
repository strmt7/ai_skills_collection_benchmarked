"""Exercise real Windows process-tree cleanup, including Python venv launchers."""

import os
import sys

import pytest
from _windows_owned_python import run_python

pytestmark = pytest.mark.skipif(os.name != "nt", reason="native Windows job controls")


@pytest.mark.parametrize("case", ["normal", "timeout", "output-limit"])
def test_owned_interpreter_cleanup(tmp_path, case):
    if case == "normal":
        code = "import sys;print(sys.flags.isolated);print('native-control-complete')"
    elif case == "timeout":
        code = "import subprocess,sys,time;p=subprocess.Popen([sys.executable,'-I','-S','-B','-c','import time;time.sleep(60)']);print(p.pid,flush=True);time.sleep(60)"
    else:
        code = "import sys,time\nwhile True:\n sys.stdout.buffer.write(b'x'*65536);sys.stdout.flush();time.sleep(0.002)"
    stdout_path = tmp_path / "stdout.log"
    with stdout_path.open("xb") as stdout, (tmp_path / "stderr.log").open("xb") as stderr:
        exit_code, process = run_python(
            sys.executable,
            code,
            [],
            cwd=tmp_path,
            environment=dict(os.environ),
            stdout=stdout,
            stderr=stderr,
            timeout=2 if case == "timeout" else 15,
            output_limit=32768 if case == "output-limit" else 8 * 1024 * 1024,
        )
    assert process["windows_job"] and process["real_interpreter_gated_before_site"]
    assert process["active_processes_after_cleanup"] == 0
    if case == "normal":
        assert exit_code == 0 and process["termination_reason"] is None
        assert stdout_path.read_text().splitlines() == ["1", "native-control-complete"]
    elif case == "timeout":
        assert exit_code == 124 and process["termination_reason"] == "timeout"
        assert int(stdout_path.read_text().strip()) > 0  # The descendant actually started.
    else:
        assert exit_code == 125 and process["termination_reason"] == "output_limit"
        assert stdout_path.stat().st_size > 32768
