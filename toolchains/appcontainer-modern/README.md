# Confined grading with pinned dependencies

Use this Windows x64 evaluator to grade a collected validator without importing
its code into the process holding expected results. It runs a capability-free
AppContainer with the pinned CPython runtime and a separately verified,
read-only dependency graph. These controls assess the validator fixture; they
are not a coding-agent performance score.

From an intact checkout with Python 3.11 or newer:

```powershell
python tools/appcontainer_runtime.py setup --home .venv/appcontainer-native
python tools/appcontainer_dependencies.py setup --home .venv/appcontainer-dependencies
python tools/grade_agent_submission.py benchmarks/agent-effectiveness/graders/artifact_validator.py <submission> --fixture . --revision <full-commit> --runtime-home .venv/appcontainer-native --dependency-home .venv/appcontainer-dependencies --output .venv/grading-run
```

Use new dedicated paths for setup and each grading run. Dependency setup can
use previously downloaded exact archives with `--archive-dir <directory>`;
all archive bytes, the deterministic bundle and the extracted file graph are
checked against [source.json](source.json). Setup extracts the unchanged pure
Python PyYAML sources and their license from the pinned upstream archive; it
does not run package build scripts. Other dependencies come from pinned public
wheels, with their included licenses. The sandbox runtime and dependency graph
are leased and checked before and after grading.

The submitted validator is collected as one file. Its helper modules and the
catalog, scenario and schema inputs come from the specified immutable fixture
commit, not from the submitted workspace. Only that bounded API fixture is
supported. The controller holds expected results outside the candidate process;
it retains native observations and records the dependency bundle and source
hashes. See the [runtime guide](../appcontainer/README.md) for resource and
Windows AppContainer limitations.

The historical development-v2 protocol and its recorded results remain frozen.
Its former host-process grader was not a security boundary; current grading
requires explicit sandbox configuration, and the old protocol's hashes prevent
it from being rerun against the changed grading code. A new experiment requires
its own frozen protocol and independent evidence.
