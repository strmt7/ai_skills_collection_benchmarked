import hashlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = "def eligible(value, minimum):\n    return value >= minimum\n\ndef public_entrypoint(value):\n    return eligible(value, 10)\n"
CONFIG = '[tool.mutmut]\nsource_paths=["src/"]\npytest_add_cli_args_test_selection=["tests/"]\nuse_setproctitle=false\n[tool.pytest.ini_options]\npythonpath=["src/"]\n'
WEAK = "from gate import eligible\ndef test_above():\n    assert eligible(11, 10) is True\n"
STRONG = (
    "from gate import eligible\ndef test_above():\n    assert eligible(11, 10) is True\n"
    "\ndef test_boundary_and_below():\n    assert eligible(10, 10) is True\n    assert eligible(9, 10) is False\n"
)


def command(args, root, env, timeout=90):
    result = subprocess.run(args, cwd=root, env=env, capture_output=True, text=True, timeout=timeout)
    return {"args": args, "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def run(request):
    env = dict(
        os.environ, HOME="/tmp", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", NO_COLOR="1", TERM="dumb", OMP_NUM_THREADS="1"
    )
    report = {
        "python": sys.version,
        "versions": {
            name: metadata.version(name) for name in ("mutmut", "trailmark", "tree-sitter-language-pack", "tree-sitter")
        },
        "source_sha256": hashlib.sha256(SOURCE.encode()).hexdigest(),
        "config_sha256": hashlib.sha256(CONFIG.encode()).hexdigest(),
        "campaigns": {},
    }
    with tempfile.TemporaryDirectory(prefix="mutation-campaign-") as temporary:
        for name, tests in (("weak", WEAK), ("strong", STRONG)):
            root = Path(temporary) / name
            (root / "src").mkdir(parents=True)
            (root / "tests").mkdir()
            (root / "src/gate.py").write_text(SOURCE)
            (root / "tests/test_gate.py").write_text(tests)
            (root / "pyproject.toml").write_text(CONFIG)
            baseline = command([sys.executable, "-m", "pytest", "-q"], root, env)
            assert baseline["exit_code"] == 0, baseline
            campaign = {
                "tests_sha256": hashlib.sha256(tests.encode()).hexdigest(),
                "baseline": baseline,
                "interfaces": [],
            }
            if name == "weak":
                for args in (
                    ["mutmut", "run", "--paths-to-mutate", "src"],
                    ["mutmut", "run", "--runner", "pytest"],
                    ["mutmut", "junitxml"],
                ):
                    campaign["interfaces"].append(command(args, root, env))
                campaign["trailmark"] = command(["trailmark", "analyze", "src"], root, env, 30)
            campaign["run"] = command(["mutmut", "run", "--max-children", "1"], root, env)
            if campaign["run"]["exit_code"] == 0:
                campaign["results"] = command(["mutmut", "results", "--all", "true"], root, env)
                campaign["export"] = command(["mutmut", "export-cicd-stats"], root, env)
                campaign["stats"] = json.loads((root / "mutants/mutmut-cicd-stats.json").read_bytes())
                campaign["metadata"] = {
                    path.relative_to(root).as_posix(): json.loads(path.read_bytes())
                    for path in sorted((root / "mutants").rglob("*.meta"))
                }
            assert (root / "src/gate.py").read_text() == SOURCE
            assert (root / "tests/test_gate.py").read_text() == tests
            report["campaigns"][name] = campaign
    return report
