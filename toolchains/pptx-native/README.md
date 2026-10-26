# Native PPTX retention controls

This optional Windows x64 CPython 3.14 environment runs the actual pinned PPT
Master converters against one deterministic, independently authored three-slide
PPTX. It requires no coding agent, API key or model service. It does not install
the catalog or qualify all presentation workflows.

From the catalog checkout, create a disposable environment with Python 3.14 and
install its complete wheel graph:

```powershell
python -m venv .venv/pptx-controls
.venv/pptx-controls/Scripts/python.exe -m pip install --require-hashes --only-binary=:all: -r toolchains/pptx-native/requirements.txt
.venv/pptx-controls/Scripts/python.exe -m pip check
```

Supply two separate Git checkout roots and their exact commits. The controller
checks every selected working file against its committed blob, rejects ignored
and untracked package inputs, and freezes the fixture, task, evaluator, controller,
dependency lock, source manifests and Windows process-control helper before
execution. Keep output outside both source checkouts and choose a new directory
each time. For the reviewed pair:

```powershell
.venv/pptx-controls/Scripts/python.exe tools/run_pptx_retention_controls.py `
  --baseline-source $baselineCheckout --baseline-commit a50758ac29ec027e85966db33e2ae80031446756 `
  --candidate-source $candidateCheckout --candidate-commit 622bf0148bca4f697b0184322c7e2aa2a04520a2 `
  --output .venv/pptx-results --json
python tools/run_pptx_retention_controls.py --check --output .venv/pptx-results --json
```

The source roots are caller-selected paths. Use command-scoped
`git -c core.autocrlf=false` for checkout so Git does not alter committed bytes.
The [Windows workflow](../../.github/workflows/pptx-retention-controls.yml)
shows complete source preparation. It runs both real attribution guards;
no guard is bypassed. Inherited provider credentials are excluded from child
environments. Python audit controls deny network, subprocess creation and writes
outside each owned output directory; these controls are not an OS sandbox.
Windows jobs own the real interpreter before site initialization and remove its
descendants on completion, timeout or excessive native output.
Only reviewed public source should be executed.

Nine semantic checks cover slide-local text, table cells, notes, grouping,
hyperlinks, chart/category associations including zero, XY coordinates and
Office14 Choice text. CLI completion and unchanged input add two execution
checks. Negative controls corrupt associations while retaining the same tokens,
or tamper with recorded provenance, logs and outputs. `--check` recomputes the
semantic results and checks retained digests without loading the PPTX SDK or
rerunning source programs. Digests provide consistency, not signed attestation.

A baseline content failure is retained and allowed; execution failure in either
version or any candidate control failure fails the command. Native logs and
Markdown remain in the output. This is component regression evidence, not a
rendering test, Office certification, runtime-readiness verdict for the whole
skill, security clearance or a coding-agent efficacy benchmark. No advantage
over default GPT-6.1 Sol or Karpathy instructions is measured here.
