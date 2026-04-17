# Host-Agnostic Installation

Validation does not require the original source checkouts:

```bash
python3 -m pip install -e '.[test]'
python3 tools/validate_catalog.py
python3 -m pytest
```

Catalog refresh does require source repositories. Put checkouts anywhere and point `AI_SKILL_SOURCE_ROOT` at that directory:

```bash
python3 tools/fetch_sources.py --source-root /path/to/ai_skill_sources
python3 tools/build_catalog.py --source-root /path/to/ai_skill_sources
```

Validation does not depend on `/tmp`, a local username, a private absolute path, or a specific host. Network-heavy benchmark execution should be performed by a separate runner that records dataset versions and artifacts.
