# Local code search with CocoIndex Code

Find relevant code locally and retain source spans that an AI agent can verify.
The provider uses a pinned CPU embedding model and needs no API key, MCP
registration or particular AI client.

## Install and search

From a clone on Windows x64, use **CPython 3.13.17**:

```powershell
py -3.13 -I tools/cocoindex_tool.py setup
py -3.13 -I tools/cocoindex_tool.py check
py -3.13 -I tools/cocoindex_tool.py index --corpus .venv/semantic/tasks-a --prefix tools --prefix docs
py -3.13 -I tools/cocoindex_tool.py search --corpus .venv/semantic/tasks-a --query "Where is source freshness verified?" --limit 5 --output .venv/research/search-a.json
```

An explicit path to that interpreter also works. Packages, model downloads,
profiles and indexes stay inside this clone's `.venv`; setup preserves other
repositories' providers and configuration. Create fresh caches on each host.

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

The default provider cache is keyed to its pinned inputs. Use
`--home .venv/agent-tools/<name>` **before** the command to choose another private
profile. If setup is interrupted, inspect the named logs and select a new
profile; partial installations are never silently replaced.

## Supported provider

This is the explicitly identified `0.2.42+catalog.local1` build of
[CocoIndex Code 0.2.42](https://github.com/cocoindex-io/cocoindex-code).
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
