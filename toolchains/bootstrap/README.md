# Automatic validation setup

Run repository tooling on Windows x64 without installing Python or development
tools globally:

```powershell
.\dev.ps1 doctor
.\dev.ps1 python -m pytest -q -n 2
.\dev.ps1 python -m ruff check tools tests
.\dev.ps1 cocoindex check
.\dev.ps1 crawl4ai check
.\dev.ps1 codex
```

The validation profile provisions its complete tested toolset automatically.
Downloads and packages have pinned hashes. A portable PowerShell runtime, Python
environments, Git and shell tools, Node and the JDK stay in an owned cache for this
checkout. Windows PowerShell starts setup using managed APIs; the admitted portable
runtime compiles and runs the native helpers, including when temporary paths
contain spaces, apostrophes or Unicode. Setup requires
network access initially, checks actual readiness and reuses admitted installations.

No administrator access, global packages, persistent PATH changes, registry
registration, shell-profile edits or specific AI client are required. Existing
profiles are preserved when a missing or changed component needs recovery.
Concurrent setup requests share one installation.

`codex` provisions the pinned stable benchmark CLI from its official npm platform
package, its complete payload and source licenses, checks its version, and returns its executable and runtime
read-root paths as JSON. It installs no Python environment or global application
and accepts no execution arguments. Use the returned paths for model-free
context qualification; model trials remain disabled until the complete runner
boundary is qualified. Provisioning the CLI does not authorize a model request.

The package is extracted with the admitted PowerShell runtime's managed tar
reader. Setup verifies every declared file and rejects missing, additional,
duplicate or linked members. The CLI profile does not require npm or a host
archive utility. Native controls verify fresh setup, reuse, helper and license
recovery, concurrent callers and refusal to execute agent arguments through
this provisioning operation. A version check alone does not establish working
agent tools; file-editing and image-reading controls remain part of runtime
qualification.

Temporary files use a separate owned directory in the operating system's
temporary location. Each operation records its location with the diagnostics.

The CLI defaults to this checkout's `.venv/cli` cache. Other bootstrap profiles
use Windows' local application-data location. Choose another writable location
with `--cache-root PATH` before the operation. Native
tools must support that location; readiness rejects a path where their helper
discovery fails. The script respects the host's execution policy.

Custom CLI caches must pass the native context and file-tool controls before
benchmark use. On the qualification host, identical admitted CLI bytes passed
those controls in the checkout cache but failed file-helper launches in an
external application-data cache. Those failures remain retained; the underlying
external-cache limitation is not established as repaired. A successful install
and version query do not qualify sandboxed agent execution at another location.

Source pins, complete licenses, runtime checks and private diagnostic records
support reproducible maintenance. Use the repository's development guide for
the full quality gates and [local code search instructions](../cocoindex-code/README.md). Component
qualification does not establish coding-agent benchmark gains or release readiness.

To qualify setup from a fresh cache, run `./tests/qualify_windows_bootstrap.ps1`
from the checkout. It checks installation, reuse, missing packages and tools,
concurrent callers, command arguments, process limits and preservation of an
unowned cache. The controls use a private Unicode temporary path and verify
recovery when a required PowerShell module is missing. They also cover
single-argument commands and Windows extended-path spelling for the engine. Records stay under `.venv/bootstrap-qualification/`; each run uses
a separate owned runtime cache. The [Windows setup workflow](../../.github/workflows/bootstrap.yml)
runs the same controls and retains their diagnostics. The code-search workflow
exercises automatic CocoIndex installation and retrieval. The
[crawler workflow](../../.github/workflows/crawl4ai-provider.yml) checks source
builds, automatic setup, native browser controls and reuse. Each provider has
its own isolated profiles and verifies its complete declared runtime inputs.

The portable shell is pinned in `powershell.json` to Microsoft's stable Windows
x64 ZIP, its publisher-reported SHA-256 and every extracted file. No installation,
remoting or policy-registration scripts from that archive are run. Setup uses no
host PowerShell 7 installation, disables its update and telemetry checks in the
child process, and keeps module discovery and its analysis cache in the owned
installation. The original process environment is restored after handoff.

Development commands inherit no API credentials by default. When a command needs
one, select its existing environment variable explicitly before the operation:

```powershell
.\dev.ps1 --credential-env PROVIDER_TOKEN python tools/your_command.py
```

Repeat `--credential-env` for additional declared variables, up to 16. Only their
names enter the command line; values are passed to the selected development
process without printing them. Empty, malformed, duplicate and runtime-reserved
selections are rejected. These settings change neither the parent environment
nor persistent host configuration. Keep credentials out of scripts and reports.
