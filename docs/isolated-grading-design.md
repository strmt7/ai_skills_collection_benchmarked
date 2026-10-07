# Isolated grading: qualification and remaining work

The completed protocol-v2 comparison used a separate host Python process.
It did not prevent submitted code from reading host files or inspecting its
in-process grader. Those results remain unchanged and retain that limitation.

An actual Docker Desktop Linux engine is available. The official Python 3.14.8
slim image was pulled and resolved to the immutable manifest digest:

`python@sha256:89fb7d3da20043c370643435258bdd7ab755d326d359001d02988ed15ae5219e`

The basic runtime probe ran that digest with disabled networking, a read-only
root, UID/GID 65534, all capabilities dropped, no new privileges, one CPU,
512 MiB memory with the same combined memory/swap limit, 64 PIDs, and a bounded
nonexecuting temporary filesystem. It returned Python 3.14.8 and UID/GID 65534;
temporary directory creation succeeded. The result is recorded in
`artifacts/research/2026-10-02/isolated-python-runtime-probe.json`.
The image pull and probe did not alter other repositories or running containers.
This initial result was a basic runtime probe. A subsequent bounded invocation
backend and actual-engine controls are recorded below. Neither establishes a
container escape/security certification or a complete agent trial protocol.

The next backend must keep the trusted supervisor and expected outcomes outside
the submitted-code container. Mount only the checked submission and a small
public invocation worker, both read-only. Do not mount the whole repository,
user home, model caches, Docker socket, authentication material or grader files.
Send only case inputs and fixture availability over a bounded JSON protocol;
never send expected scores. Keep stdout/stderr, request sizes, CPU, memory,
process counts and deadlines bounded. Terminate and remove only containers
created by that invocation; record cleanup failures and their exact identities.

Qualify known-good, known-bad, malformed-output and nonterminating controls;
verify denied writes, unavailable host sentinel data and absent network access.
Test transport and result parsing independently of candidate skill wording.
Changing runtime, isolation, worker or grading methodology requires a new
immutable protocol and new matched comparisons; do not pool it with v2 to
manufacture a gain.

## Implemented backend and controls

`tools/isolated_python.py` stages only explicitly named regular files and a
public invocation worker. It rejects unsafe paths, links/reparse parents, case
collisions and oversized inputs. Candidate code receives case inputs but no
expected answers. The host parses bounded output and scores it separately.
Containers use the pinned image, read-only submission/worker mounts, disabled
networking and IPC, dropped capabilities, no new privileges, bounded resources
and temporary storage, and disabled persistent Docker logs. Configuration is
inspected before start. Cleanup verifies the unique ownership label and exact
container identity before removal; unrelated containers are not selected.

`tools/qualify_isolated_python.py` provides nine actual-engine controls:
correct/incorrect results, missing functions, malformed output, nontermination,
stdout/stderr floods, leftover children, and filesystem/network/identity checks.
All pass again in `isolated-backend-controls-v5.json` after immutable dependency
image support was added. `--check` revalidates
recorded input hashes, complete denominators and observed isolation settings;
it does not rerun the current host. Earlier receipts remain available. The first
child control incorrectly expected a timeout although Docker terminated the
child when its parent exited. The corrected control requires verified cleanup
with either completion or timeout, rather than hiding the first result.

The default image remains the qualified pinned Python base. Explicit dependency
images must use a complete immutable local `sha256:` image ID. Inspection checks
both the requested image and resolved ID; every original isolation/resource
constraint still applies. A complete unchanged stable Atheris wheel was installed
offline into such an image and exercised with eight actual source/engine controls.
Dependency installation, pure-Python engine controls and native sanitizer
qualification are distinct; the latter remains unfinished.

The default profile has one CPU, 512 MiB and 64 PIDs. `skillsbench-tfidf` uses
the published task's eight CPUs and 4 GiB, with a 256-PID bound. Four reference
cases ran under that profile with complete external structure comparison in
`tfidf-grader-runtime-controls-v3.json`. The public reproducer is
`benchmarks/agent-effectiveness/controls/tfidf_grading.py`. Its first published
version introduced an indentation error; the failed v2 receipt is retained.
These controls qualify invocation/comparison contracts, not a task speedup or
an agent score. Full performance fixtures, hosted integration and fresh matched
agent comparisons remain unfinished.

Primary operational references are the
[official Python image](https://hub.docker.com/_/python) and
[Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).

For prospective Rust cases, the inspected host toolchain is 1.98.1, while the
[official stable release notes](https://doc.rust-lang.org/stable/releases.html)
identify 1.99.0, released 1 October 2026. An isolated current toolchain is needed
before qualified Rust comparisons. Do not change another repository's active
toolchain while preparing this collection's fixtures.
