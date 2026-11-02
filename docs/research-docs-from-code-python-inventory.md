# Python documentation inventory

The pinned docs-from-code Python extractor misses a Flask `route`, treats an
unrelated `get` decorator as an HTTP route, loses function signature details,
and does not resolve the tested FastAPI router inclusion. The
[source-bound baseline review](research-docs-from-code.md) also found that
invalid source could be silently omitted.

The [maintained Python inventory](../included/repaired/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code-python-inventory/SKILL.md)
addresses those selected cases without importing the target project. Its
results are source-level candidates and explicitly report their limitations.
The tests include dynamic and unmounted routes, multiple inclusions, rebinding,
signature syntax, source encodings, parse failures and output handling.

In separate environments, selected candidates were also compared with actual
Flask 3.1.3 route rules and FastAPI 0.162.0 OpenAPI output. Flask adds HEAD and
usually OPTIONS automatically; the inventory reports the declared methods
instead. See the [Flask API](https://flask.palletsprojects.com/en/stable/api/)
and [FastAPI router guide](https://fastapi.tiangolo.com/tutorial/bigger-applications/).
This comparison covers selected owned fixtures, not all framework behavior.
The inventory does not establish runtime route coverage, repair the TypeScript
extractor, test graphify, or measure coding-agent performance.

The [qualification record](../artifacts/repaired-skill-readiness/docs-from-code-python-inventory-v1/qualification.json)
binds the tested script, cases and dependencies to five local runs. To reproduce,
create an isolated Python environment, install the appropriate hash-locked
requirements in that directory, and run:

```sh
python artifacts/repaired-skill-readiness/docs-from-code-python-inventory-v1/reproduce.py --output /new/output-directory
```

The output retains the native pytest transcript and JUnit report. The generic
type-parameter case is skipped on Python 3.11, before that syntax was added.
