# Local code search with CocoIndex Code

Find relevant code locally and retain source spans that an AI agent can verify.
The provider uses a pinned CPU embedding model and needs no API key, MCP
registration or particular AI client.

## Install and search

From a clone on Windows x64:

```powershell
.\dev.ps1 cocoindex check
.\dev.ps1 cocoindex index --corpus .venv/semantic/tasks-a --prefix tools --prefix docs
.\dev.ps1 cocoindex search --corpus .venv/semantic/tasks-a --query "Where is source freshness verified?" --limit 5 --output .venv/research/search-a.json
```

Missing Python, packages and the local model install automatically from verified,
locked inputs. The native C++ runtime is downloaded directly from Microsoft and
used inside the private installation; no global installer runs. No administrator
access, API key, global packages, persistent PATH changes, registry registration,
MCP registration or particular AI client is required.

The foundation uses an owned cache for this checkout; provider environments,
models and indexes stay in its `.venv`. `--cache-root PATH` before `cocoindex`
selects another writable foundation cache. Create fresh caches on each host.
Only the validation command provisions Node and Java.

Select only the files or directories needed for the task with repeated
`--prefix` arguments. Only UTF-8 inputs without NUL bytes and at most 4 MiB enter
the text corpus. Git's untracked ignored files are omitted. Keep credentials and
unrelated private material out of the selected sources. Searches run locally
with the admitted model.

Read the native search JSON and confirm relevant hits in the current source.
A ranking is not a completeness check. `--path 'tools/**'` restricts a search to
a source scope. Use a new output filename for each receipt.

## Refresh and recovery

Source changes invalidate the corpus binding. Preserve earlier evidence and
index the relevant prefixes at a new corpus path. To verify an existing index,
repeat its `index` command with `--check`.

Each command verifies the selected provider before use. Missing or changed
packages trigger a fresh isolated installation; earlier profiles and failure
diagnostics are preserved. Concurrent setup requests share one installation.
The cache belongs to this checkout and refuses unrelated existing data.
Replacement profiles share an owned package-download cache. Installed packages
remain isolated, and every installation still requires the pinned hashes.

A valid existing index keeps its original model binding across package recovery;
the model's exact inventory, bytes and local settings are verified again. Changed
source or model contents require a new corpus, preserving the earlier evidence.

The low-level `tools/cocoindex_tool.py` remains available for explicit provider
qualification with an admitted CPython 3.13.18 interpreter. Its `--home` option
selects a separate directory under `.venv`; automatic setup manages its own
profiles and does not adopt that directory.

## Supported provider

This is the explicitly identified `0.2.43+catalog.local1` build of
[CocoIndex Code 0.2.43](https://github.com/cocoindex-io/cocoindex-code).
Its author classifies the upstream package as Alpha. The qualified mode here is
Windows x64 CPU search using CocoIndex 1.0.26 and the pinned
`Snowflake/snowflake-arctic-embed-xs` model. Cloud embeddings are unsupported.

The local build removes the unused cloud embedding dependency and disables
remote model code. This permits a normal, complete dependency installation with
the fixed `filelock` release. Upstream LiteLLM requires `filelock<4`, which
conflicts with the fixes for [the published filelock advisories](https://github.com/advisories/GHSA-567q-5qvw-pf92).
No dependency conflict or advisory is ignored.

Setup builds the exact admitted wheel, verifies provider and core files,
installs the complete hashed graphs, and checks the model's revision, sizes and
hashes. Model modules are restricted to the three pinned built-in components;
Python files and pickle weight formats are refused. Index and search processes
use private configuration and safe Python import paths.

The original Apache-2.0 [license](LICENSE),
[change notice](CATALOG_BUILD_NOTICE.txt), [source pin](source.json) and
[model pin](model.json) remain available. Advisory scans use the upstream
package identity; only the admitted install lock substitutes the local wheel.
Build and runtime graphs are audited separately because their constraints differ.

For maintenance and evidence, see the
[native qualification workflow](../../.github/workflows/cocoindex-provider.yml)
and [contributing guide](../../CONTRIBUTING.md). Component qualification and
source-bound retrieval do not establish a coding-agent benchmark advantage.
