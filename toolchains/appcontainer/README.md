# Confined validator evaluation on Windows

Use this evaluator to check a collected artifact-validator patch without loading
submitted Python in the process that holds expected verdicts. It supports the
stdlib-only validator API fixture on Windows x64. No AI client, API key, global
Python installation change or additional operating system is required.

From the repository root, using a supported Python interpreter:

```powershell
python tools/appcontainer_runtime.py setup --home .venv/appcontainer-native
python tools/appcontainer_runtime.py check --home .venv/appcontainer-native
python tools/qualify_appcontainer.py --runtime-home .venv/appcontainer-native --output .venv/appcontainer-evidence --revision <full-current-commit>
```

Setup downloads the official, unmodified CPython **3.15.2** Windows embeddable
archive. Its byte count, SHA-256 and all 39 installed files are pinned in
[source.json](source.json). The bundled Python license is retained. An exact
existing archive can be supplied with `--archive` for offline installation.
Existing installations and evidence directories are never overwritten.

To evaluate a collected patch:

```powershell
python tools/grade_validator_appcontainer.py --submission <collected-directory> --fixture . --revision <full-fixture-commit> --runtime-home .venv/appcontainer-native --output .venv/validator-run
```

Only `tools/check_benchmark_artifact.py` is collected from the submission, with
a 1 MiB limit. Catalog, scenario and schema inputs come from exact Git blobs at
the selected commit. The worker receives the current API input and optional
schema override. Expected verdicts stay in the controller. Every case uses a
fresh capability-free AppContainer with an independently attested suspended
token, Low integrity and an anonymous Windows Job assigned before execution.
Read-only mounts, a separate writable scratch directory, one active process,
256 MiB committed process memory, CPU time, wall time and output bounds constrain
execution. Only NUL input and two pipes are inherited. The controller verifies
source integrity, records native output and restores read-only ACLs.

The [native workflow](../../.github/workflows/appcontainer-controls.yml) exercises
matched normal/confined file, ACL, parent-memory and loopback controls; timeout,
output, memory and child-process limits; a reference validator and two deliberately
invalid candidates. [Retained evidence](../../artifacts/component-controls/appcontainer/result.json)
records the reference at 17/17, the caller-frame oracle probe at 0/17 and the
always-success stub at 2/17. These are component controls, **not model trials or
evidence of a skill advantage**. Earlier frozen graders and trial results retain
their original behavior and limitations.

Run `python tools/qualify_appcontainer.py --check` to verify retained source and
observation hashes and recompute verdicts from native responses. After a new
native run, `--publish <private-campaign-directory>` performs an initial admission
of explicitly selected observations; it refuses to replace existing
published evidence. Candidate scratch is never traversed for publication or
cleanup.

This is a bounded evaluator for this API fixture, not a general hostile-code
execution service. Windows AppContainer still exposes operating-system resources
granted to applications. Scratch and registry storage have no disk quota. A hard
termination of the controller kills its Job's child but can leave profile and ACL
cleanup incomplete; retain its `profile.json` and use a disposable Windows worker
for hostile submissions. Normal exit, candidate exceptions and enforced limits
have tested profile deletion, ACL restoration and zero surviving child processes.
No network capability, challenge bypass, external model or secondary agent is used.
