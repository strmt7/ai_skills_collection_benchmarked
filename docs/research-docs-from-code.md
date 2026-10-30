# Documentation extractor component review

The mirrored [docs-from-code skill](../included/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code/SKILL.md)
uses graphify as its primary method and supplies Python and TypeScript
extractors as fallbacks. This review tests the fallbacks against synthetic
source; it does not execute graphify or measure generated documentation quality.

The fixture contains a Flask `@app.route` handler, a FastAPI `@api.get` handler,
an unrelated cache object's `@cache.get` decorator, and a function with a
positional-only argument, defaults, variadic arguments and a keyword-only
argument. The original extractor found the FastAPI route, missed the Flask
route, reported the cache decorator as a GET route, and omitted the defaults,
variadic parameters and positional-only marker from the function signature.
The fixture is parsed, not executed. These are demonstrated examples, not a
complete assessment of supported frameworks or every syntax form.

The [reproducer](../artifacts/research/2026-10-30/docs-from-code-python-extractor/reproduce.py)
checks the mirrored extractor's SHA-256 and runs it in a temporary synthetic
project. Its [Windows](../artifacts/research/2026-10-30/docs-from-code-python-extractor/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/docs-from-code-python-extractor/linux-result.json)
results agree; a modified extractor was rejected. Treat its route list and
signatures as candidates to verify against source, not a complete API contract.

The TypeScript fallback did not start in isolated Windows and Linux installs
of the skill's declared dependencies: `ts-node` reported TS2353 for an
unsupported project option. A temporary diagnostic copy changed only that
option, allowing a synthetic fixture to be analyzed. It found `/api/ping`,
missed a Next.js `app/products/route.ts` and a JavaScript route file, and
reported a cache lookup as a GET route. The [Next.js route convention](https://nextjs.org/docs/app/getting-started/route-handlers)
allows route handlers in nested `app` directories. The fixture itself was not executed.
This diagnostic does not establish a complete fix for the extractor.

The [TypeScript control](../artifacts/research/2026-10-30/docs-from-code-typescript-extractor/reproduce.py)
records its [Windows](../artifacts/research/2026-10-30/docs-from-code-typescript-extractor/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/docs-from-code-typescript-extractor/linux-result.json)
results, source hashes and resolved dependency versions. For reproduction,
copy the mirrored `package.json` and the retained
[qualification lock](../artifacts/research/2026-10-30/docs-from-code-typescript-extractor/qualification-package-lock.json)
to a private directory as `package.json` and `package-lock.json`, run
`npm ci --ignore-scripts` there, then run the control with `--provider` and
`--extractor` pointing to that directory and the mirrored TypeScript file.

The mirror is pinned to
[`bc01f7c1`](https://github.com/Varnan-Tech/opendirectory/tree/bc01f7c1c31f0af54c2924c1ec1abbb472ab1df4/packages/cli/skills/docs-from-code).
At the observed upstream main commit
[`caac7cda`](https://github.com/Varnan-Tech/opendirectory/tree/caac7cda5621e289591e4e74b400e66ac72ad25b/skills/docs-from-code),
the skill had moved and its instruction file differed, but both extractor
scripts and their TypeScript manifest were the same Git blobs. [Source identity evidence](../artifacts/research/2026-10-30/docs-from-code-python-extractor/source-evidence.json)
records those revisions and API capture digests. The source lock was not
changed; upgrading the full source requires a separate review. No agent
efficacy score is claimed.
