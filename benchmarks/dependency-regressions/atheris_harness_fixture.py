"""Owned source-contract controls; no benchmark task/agent quality is scored."""

import json
import os
import re
import subprocess
import sys
import tempfile
import traceback
import types
from importlib.metadata import version
from pathlib import Path


def snippet(text, heading):
    section = text.split(heading, 1)[1]
    return re.search(r"```python\n(.*?)\n```", section, re.DOTALL).group(1)


def load_harness(code):
    namespace = {"__name__": "source_control"}
    exec(compile(code, "original-skill-example.py", "exec"), namespace)
    return namespace


def run(_):
    try:
        return controls()
    except Exception:
        return {"error": traceback.format_exc(), "agent_processes": 0}


def controls():
    sys.path.insert(0, str(Path(__file__).parent / "vendor"))
    import atheris
    import urllib3

    original = (Path(__file__).parent / "original-SKILL.md").read_text("utf-8")
    checks = []
    assert version("atheris") == "3.1.0"
    assert not hasattr(atheris, "__version__")
    checks.append("original_version_verification_raises_attribute_error")
    assert not (Path(atheris.__file__).parent / "asan_with_fuzzer.so").exists()
    assert (Path(atheris.path()) / "asan_with_fuzzer.so").is_file()
    checks.append("original_dynamic_preload_path_misses_installed_sanitizer_library")

    namespace = load_harness(snippet(original, "### Example: Pure Python Parser"))
    observed = []

    def parse(text):
        observed.append(text)
        return json.loads(text)

    namespace["json"] = types.SimpleNamespace(loads=parse)
    for data in [b'"a"', b'"\xffa"']:
        namespace["test_one_input"](data)
    assert observed == ['"a"', '"a"']
    checks.append("json_ignore_decode_collapses_distinct_input_bytes")

    namespace = load_harness(snippet(original, "### Example: HTTP Request Parsing"))
    responses = []
    reads = []

    class BodyReader(urllib3.HTTPResponse):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            responses.append(self)

        def read(self, *args, **kwargs):
            result = super().read(*args, **kwargs)
            reads.append(result)
            return result

    namespace["HTTPResponse"] = BodyReader
    wire = b"HTTP/1.1 201 Created\r\nContent-Length: 2\r\n\r\nok"
    namespace["test_one_input"](wire)
    assert reads == [wire] and responses[0].status == 0 and dict(responses[0].headers) == {}
    checks.append("http_example_reads_wire_as_body_without_parsing_status_or_headers")

    class BrokenBodyReader:
        def __init__(self, **_):
            pass

        def read(self):
            raise RuntimeError("owned unexpected target defect")

    namespace["HTTPResponse"] = BrokenBodyReader
    namespace["test_one_input"](b"x")
    checks.append("http_harness_swallows_injected_unexpected_runtime_error")

    provider = atheris.FuzzedDataProvider(b"")
    assert provider.ConsumeIntInRange(1, 1000) == 1
    assert provider.ConsumeBytes(8) == b"" and provider.ConsumeBool() is False
    assert provider.remaining_bytes() == 0
    checks.append("real_provider_empty_input_uses_degenerate_defaults")

    probe = """import atheris,sys
calls=0
@atheris.instrument_func
def target(data):
    global calls
    assert isinstance(data,bytes) and len(data)<=8
    calls+=1
atheris.Setup(sys.argv,target)
try:
    atheris.Fuzz()
finally:
    print("OWNED_CALLS="+str(calls))
"""
    with tempfile.TemporaryDirectory(prefix="atheris-harness-") as temporary:
        stage = Path(temporary)
        harness = stage / "probe.py"
        harness.write_text(probe, encoding="utf-8")
        command = [sys.executable, "-I", "-B", str(harness), "-atheris_runs=64", "-max_len=8", "-seed=1"]
        bounded = subprocess.run(command, cwd=stage, capture_output=True, timeout=15, check=False)
        stdout = bounded.stdout.decode("utf-8", errors="replace")
        stderr = bounded.stderr.decode("utf-8", errors="replace")
        assert bounded.returncode == 0 and "OWNED_CALLS=64" in stdout, (bounded.returncode, stdout, stderr)
        assert "INITED cov:" in stderr
        checks.append("real_instrumented_engine_completes_64_bounded_calls")
        harness.write_text(snippet(original, "## Quick Start"), encoding="utf-8")
        seed = stage / "owned-seed"
        seed.write_bytes(b"FUZZ")
        crashed = subprocess.run(
            [sys.executable, "-I", "-B", str(harness), str(seed), "-runs=1", "-seed=1"],
            cwd=stage,
            capture_output=True,
            timeout=15,
            check=False,
        )
        crash_stderr = crashed.stderr.decode("utf-8", errors="replace")
        crash_stdout = crashed.stdout.decode("utf-8", errors="replace")
        assert crashed.returncode != 0 and "RuntimeError: You caught me" in crash_stdout + crash_stderr, (
            crashed.returncode,
            crash_stdout,
            crash_stderr,
        )
        checks.append("original_quickstart_replays_known_seed_python_exception")
    return {
        "checks": checks,
        "platform": sys.platform,
        "uid": os.getuid(),
        "python_version": sys.version.split()[0],
        "atheris_version": version("atheris"),
        "urllib3_version": urllib3.__version__,
        "bounded_engine": {"returncode": bounded.returncode, "stdout": stdout, "stderr": stderr},
        "known_seed_replay": {"returncode": crashed.returncode, "stdout": crash_stdout, "stderr": crash_stderr},
        "temporary_directory_removed": not stage.exists(),
        "native_target_or_sanitizers_qualified": False,
        "agent_processes": 0,
    }
