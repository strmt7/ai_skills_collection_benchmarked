# Source-verified CocoIndex navigation

Use semantic search to locate candidates, then inspect exact source and nearby
tests. The development corpus selects `included/skills`, `included/improved`
and `tools`; it excludes owner repositories and sealed benchmark holdouts.
Test navigation remains a separate step because `tests` is outside this corpus.

The current qualified provider is CocoIndex 1.0.25 / CocoIndex Code 0.2.42 on
Python 3.14.8, with a hash-bound local CPU model, offline inference and usage
tracking disabled. Complete selected-resource coverage is recorded separately
from retrieval behavior. It does not establish model or skill effectiveness.

Use [search_semantic_corpus.py](../tools/search_semantic_corpus.py) with the
explicit local provider and a fresh prepared corpus. For the qualified local
7 October development environment:

```powershell
& .venv/environments/latest-tools/Scripts/python.exe tools/search_semantic_corpus.py `
  --corpus .venv/semantic-corpus/full-resources-v8 `
  --python .venv/environments/cocoindex-current/Scripts/python.exe `
  --provider-dir .venv/research-state/cocoindex-providers-2026-10-07 `
  --model-proof artifacts/research/2026-10-02/cocoindex-model-provision.json `
  --query "ambiguous mutation mapping zero callers false positives" `
  --path "included/improved/skills/genotoxic-current/**" --limit 3 --json
```

The adapter checks the entire selected source inventory before and after the
query, verifies the pinned model bytes, clears inherited CocoIndex host/database
mappings, and sends the literal request through the client API. Each result
must refer to selected unchanged bytes, match its one-based source lines and
requested scope, and have a finite score. Empty results are a failed navigation
check. Errors do not rewrite, install, reset or claim to repair an index.
Rebuild a stale corpus explicitly; after a diagnosed search failure, use bounded
`rg --files` / `rg -l` and exact reads to continue correctness work.

## Verified Windows CLI issue

The stock CLI passes Windows `sys.argv` through Click's default wildcard
expansion. A literal `--path included/improved/skills/genotoxic-current/**`
becomes a directory name with backslashes; remaining expanded filenames become
query words. [Actual dispatch controls](../artifacts/research/2026-10-07/cocoindex-windows-literal-path-dispatch-controls.json)
verify both changes and show that explicit argument lists preserve the request.
The client API also preserves it, as verified against actual source spans.
No upstream provider file was edited.

Earlier receipts retain empty CLI results. Three initially mislabeled
`client-repeat` blocks also ran the CLI because the probe used
`startswith('cli')`; the dispatch receipt corrects those labels. The corrected
CLI-versus-client receipt records successful client retrieval alongside failing
CLI filtering. An owned daemon restart did not repair CLI filtering. The
documented cause is argument expansion, not a damaged index or model-quality
result. Similarity scores remain uncalibrated routing hints.

The final adapter adds explicit rejection of boolean counts/coordinates/scores
and malformed hit objects. Twenty-one focused controls and the 593-test suite
pass. The v7 receipt preserves the earlier adapter state; v8 binds the final
adapter source. Exact probe/refresh reproducers are retained alongside their
receipts. They require the named ignored provider/model/source inputs and fresh
output paths; they are evidence recipes, not standalone installers or model
benchmark runners.

[Ten final runtime controls](../artifacts/research/2026-10-07/cocoindex-adapter-v8-runtime-controls.json)
verify three literal scoped queries and all nine returned passages against the
current provider, corpus digest and exact source. The tools query also returns
general infrastructure text; this demonstrates why verified source identity
must not be confused with independently measured relevance or task usefulness.
