"""Source-helper boundaries using owned command spies; no Kubernetes cluster is contacted."""

import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

SPY = r"""
import json,os,sys
args=sys.argv[1:]
with open(os.environ["SPY_LOG"],"a") as stream:stream.write(json.dumps(args)+"\n")
mode=os.environ["SPY_MODE"]
if mode=="events-denied" and args[:2]==["get","events"]:
 print("Error from server (Forbidden): cannot list events",file=sys.stderr);sys.exit(23)
if mode=="redis-denied" and "app.kubernetes.io/name=redis" in args:
 print("Error from server (Forbidden): cannot list redis pods",file=sys.stderr);sys.exit(23)
if mode=="metrics-denied" and args[:1]==["top"]:
 print("Error from server (Forbidden): cannot list metrics",file=sys.stderr);sys.exit(23)
if "app.kubernetes.io/name=redis" in args:print("redis-owned")
elif args[:1]==["exec"]:
 if "XLEN" in args: print("14")
 elif "INFO" in args: print("used_memory_human:1M\naof_enabled:1\nconnected_clients:1")
 elif "mount" in args: print("/data")
 else: print("0")
elif args[:2]==["get","pods"] and any("jsonpath=" in arg for arg in args):pass
else:print("owned diagnostic fixture")
"""


def run(_):
    checks = []
    cases = {}
    with tempfile.TemporaryDirectory(prefix="diagnosis-spies-", dir="/tmp") as temporary:
        stage = Path(temporary)
        spy = stage / "kubectl-spy.py"
        spy.write_text(SPY, encoding="utf-8")
        bash_env = stage / "owned-bash-environment.sh"
        bash_env.write_text(
            f'kubectl() {{ {shlex.quote(sys.executable)} {shlex.quote(str(spy))} "$@"; }}\n', encoding="utf-8"
        )
        for mode in ("healthy", "events-denied", "redis-denied", "metrics-denied"):
            log = stage / f"{mode}.jsonl"
            environment = os.environ | {
                "BASH_ENV": str(bash_env),
                "SPY_MODE": mode,
                "SPY_LOG": str(log),
                "BUTTERCUP_NAMESPACE": "owned-control",
            }
            completed = subprocess.run(
                ["/bin/bash", str(Path(__file__).with_name("original-diagnose.sh"))],
                env=environment,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            assert log.exists(), (completed.returncode, completed.stdout, completed.stderr)
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            cases[mode] = {
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "calls": calls,
            }
        assert cases["healthy"]["returncode"] == 0
        checks.append("original_helper_completes_against_owned_command_spy")
        assert cases["events-denied"]["returncode"] == 23
        checks.append("warning_events_permission_failure_aborts_snapshot")
        assert cases["redis-denied"]["returncode"] == 0
        assert "No redis pod found" in cases["redis-denied"]["stdout"]
        assert "Forbidden" not in cases["redis-denied"]["stdout"] + cases["redis-denied"]["stderr"]
        checks.append("redis_permission_failure_is_misreported_as_missing_pod")
        assert cases["metrics-denied"]["returncode"] == 0
        assert "metrics-server not available" in cases["metrics-denied"]["stdout"]
        assert "Forbidden" not in cases["metrics-denied"]["stdout"] + cases["metrics-denied"]["stderr"]
        checks.append("metrics_permission_failure_is_misreported_as_unavailable_server")
        calls = cases["healthy"]["calls"]
        assert all("--request-timeout" not in " ".join(call) for call in calls)
        checks.append("helper_requests_have_no_explicit_api_timeout")
        assert ["top", "nodes"] in calls
        assert all("owned-control" in call for call in calls if call != ["top", "nodes"])
        checks.append("namespace_override_is_used_except_cluster_scoped_node_metrics")
    return {
        "checks": checks,
        "cases": cases,
        "uid": os.getuid(),
        "platform": sys.platform,
        "python_version": sys.version.split()[0],
        "temporary_directory_removed": not stage.exists(),
        "cluster_contacted": False,
        "agent_processes": 0,
    }
